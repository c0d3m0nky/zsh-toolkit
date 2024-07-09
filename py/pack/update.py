import os
import subprocess
from pathlib import Path

from git import Repo

_basedir = Path(os.environ.get('ZSHCOM__basedir'))


def _sh(cmd: str, check=False, suppress_error=False) -> str:
    if suppress_error:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=check)
    else:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=check)

    return res.stdout.decode('utf-8').strip()


def is_behind_origin() -> bool:
    resp = _sh('git status | grep -P "Your branch is behind .+ by (\d+) commit"')

    return bool(resp)

def main():
    repo = Repo(_basedir)
    repo.remotes.origin.fetch()
    diffs = repo.git.diff(f'origin/{repo.active_branch.name}')


if __name__ == '__main__':
    main()
