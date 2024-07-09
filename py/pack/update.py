import os
import subprocess
import re
from pathlib import Path
from typing import Union

from git import Repo

_basedir = Path(os.environ.get('ZSHCOM__basedir')).resolve()


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
    repo = Repo(_basedir)
    up_to_date = False

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
        else:
            up_to_date = True

    if up_to_date:
        print('Repo successfully updated')
        

    # diffs = repo.git.diff(f'origin/{repo.active_branch.name}')


if __name__ == '__main__':
    main()
