from git import Repo
from tap import Tap
from pathlib import Path
from datetime import datetime

from zsh_toolkit_py.shared.cli_args import PathArg


class Args(Tap):
    repository: Path

    def configure(self) -> None:
        self.description = 'Auto-Commit Git Repository'
        self.add_argument('repository', type=PathArg, nargs='?', help='Repo path')


_args = Args().parse_args()
_branch_prefix = 'auto_commit'


def main() -> None:
    repo_path = _args.repository.expanduser().resolve()
    repo = Repo(repo_path)

    print(f'Fetching repo at {repo_path.as_posix()}')
    repo.remotes.origin.fetch()
    print('Getting repo status')
    is_dirty = repo.is_dirty() or bool(repo.index.diff(None)) or bool(repo.untracked_files)
    now = datetime.now()

    current_branch = repo.active_branch

    if is_dirty:
        print('Repo is dirty')
        print(repo.git().status())

        if not current_branch.name.startswith(_branch_prefix):
            branch_name = f'{_branch_prefix}/{now.strftime("%y-%m-%d--%H-%M")}'
            print(f'Creating branch {branch_name}')
            current_branch = repo.create_head(branch_name)
            print(f'Checking out branch {branch_name}')
            current_branch.checkout()

        print('Adding files')
        repo.git.add(A=True)
        print('Committing files')
        repo.git.commit(m=f'Auto commit {now.strftime("%y-%m-%d--%H-%M")}')
        print('Pushing commit')
        repo.git.push('--set-upstream', 'origin', current_branch)
    else:
        print('Repo is clean')


if __name__ == '__main__':
    main()
