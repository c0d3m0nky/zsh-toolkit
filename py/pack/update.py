import os
import subprocess
import re
from pathlib import Path

from git import Repo
from tap import Tap

from utils import parse_bool, shellcolors

_basedir = Path(os.environ.get('ZSHCOM__basedir')).resolve()


class Args(Tap):
    dependencies: bool

    def configure(self) -> None:
        self.description = 'Update zsh-toolkit'
        self.add_argument("-d", "--dependencies", action='store_true', help="Only update dependencies", default=False)


def _sh(cmd: str, check=False, suppress_error=False) -> str:
    if suppress_error:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=check, cwd=_basedir)
    else:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=check, cwd=_basedir)

    return res.stdout.decode('utf-8').strip()


_rx_local_changes = re.compile(r'(Changes not staged for commit|Changes to be committed)', re.MULTILINE)
_rx_behind_origin = re.compile(r'Your branch is behind .+ by (\d+) commits?', re.MULTILINE)
_rx_ahead_origin = re.compile(r'Your branch is ahead of .+ by (\d+) commits?', re.MULTILINE)
_rx_diverged = re.compile(r'and have (\d+) and (\d+) different commits each, respectively', re.MULTILINE)


def main():
    args = Args().parse_args()

    if args.dependencies:
        ud = _basedir / '.state_update_dependencies'
        ud.touch()
        exit(0)

    repo = Repo(_basedir)
    up_to_date = False
    pulled = False

    print('Checking for updates...')
    print('')

    while not up_to_date:
        repo.remotes.origin.fetch()
        status = _sh('git status')
        behind_origin = _rx_behind_origin.search(status)
        local_changes = _rx_local_changes.search(status)
        diverged = _rx_diverged.search(status)
        ahead = _rx_ahead_origin.search(status)

        if diverged or ahead or local_changes:
            print('You have local changes, please update manually')
            break
        elif behind_origin:
            print('You\'re behind origin, updating')
            repo.remotes.origin.pull()
            pulled = True
        else:
            up_to_date = True

    (_basedir / '.state_repo_update_checked').touch()

    if up_to_date:
        print('')

        if pulled:
            (_basedir / '.state_repo_updated').touch()
            (_basedir / '.state_update_dependencies').touch()

            if parse_bool(os.environ.get('ZSHCOM_UPDATE_NORELOAD')):
                print(f'Repo successfully updated. Updates will be available in new terminal sessions or after running {shellcolors.OKCYAN}source $ZSHCOM/init.sh{shellcolors.OFF}')
            else:
                _sh('source $ZSHCOM/init.sh')
        else:
            print('Repo is up to date')


if __name__ == '__main__':

    main()
