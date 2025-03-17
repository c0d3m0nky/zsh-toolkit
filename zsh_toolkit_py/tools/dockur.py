import subprocess
import sys
from typing import Dict, Callable, List, Union

from docker import from_env as docker_from_env

from zsh_toolkit_py.shared.cli_args import BaseTap
from zsh_toolkit_py.shared.logger import Logger

from zsh_toolkit_py.models.dockur import DockerConnection

_log: Logger

YamlVal = Union[str, int, float, bool]
YamlNode = Dict[str, YamlVal]
YamlRoot = Dict[str, Dict[str, YamlNode]]


def sh(cmd: str):
    p = subprocess.Popen(cmd, shell=True)
    p.wait()


class Args(BaseTap):
    command: str
    trace: bool = False
    plan: bool = False

    def __init__(self, commands: List[str], *args, **kwargs):
        self._command_choices = commands
        super().__init__(*args, **kwargs)

    def configure(self) -> None:
        self.description = 'Docker utilities'
        self.add_argument('command', help='Helper action', choices=self._command_choices)
        self.add_plan("Don't overwrite (shows diff)")
        self.add_trace()

    def process_args(self) -> None:
        pass

    def error(self, message):
        print('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


_args: Args
_dkr: DockerConnection

_commands: Dict[str, Callable[[], None]] = {

}

if __name__ == '__main__':
    _args = Args(list(_commands.keys())).parse_args()
    _log = Logger(_args.trace, False)

    try:
        _log.trace('Connecting to docker client')
        _dkr = docker_from_env()
    except Exception as exc:
        _log.error(f'Failed to connect to docker client', exc)
        exit(1)

    _commands[_args.command]()
