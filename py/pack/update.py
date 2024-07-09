import os
import subprocess
import re
from pathlib import Path

from git import Repo

_basedir = Path(os.environ.get('ZSHCOM__basedir'))


def _sh(cmd: str, check=False, suppress_error=False) -> str:
    if suppress_error:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=check)
    else:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=check)

    return res.stdout.decode('utf-8').strip()


_rx_behind_origin = re.compile(r'Your branch is behind .+ by (\d+) commit')
_rx_diverged = re.compile(r'and have (\d+) and (\d+) different commits each, respectively')


def main():
    repo = Repo(_basedir)
    repo.remotes.origin.fetch()

    status = _sh('git status')
    behind_origin = _rx_behind_origin.match(status)
    diverged = _rx_diverged.match(status)

    diffs = repo.git.diff(f'origin/{repo.active_branch.name}')


if __name__ == '__main__':
    main()
