import enum
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Union

from utils import ShellColors


@dataclass
class LogLevel:
    value: str
    color: Union[ShellColors, None]


class LogLevels(enum.Enum):
    ERROR = LogLevel('ERROR', ShellColors.FAIL)
    WARN = LogLevel('WARN', ShellColors.WARNING)
    LOG = LogLevel('LOG', None)
    TRACE = LogLevel('TRACE', ShellColors.OFF)


class Logger:
    _trace: bool
    _inject_ts: bool
    _disable_log_color: bool
    _ts_format: str
    _log_color: ShellColors

    def __init__(self, trace: bool = False, inject_date: bool = True, ts_format: str = '%Y-%m-%d %H:%M:%S',
                 disable_log_color: bool = False, log_color: ShellColors = ShellColors.OKGREEN):
        self._trace = trace
        self._inject_ts = inject_date
        self._ts_format = ts_format
        self._log_color = log_color or ShellColors.OFF
        self._disable_log_color = disable_log_color


    def error(self, msg: str, exc: Exception = None) -> None:
        if exc:
            msg += f'\n{exc}'
            if self._trace:
                msg += f'\n{traceback.format_exc()}'

        self.log(msg, LogLevels.ERROR)

    def trace(self, msg: str) -> None:
        if self._trace:
            self.log(msg, LogLevels.TRACE)

    def warn(self, msg: str) -> None:
        self.log(msg, LogLevels.WARN)

    def log(self, msg: str, level: LogLevels = LogLevels.LOG) -> None:
        pref = (level.value.color or self._log_color) if not self._disable_log_color else ''
        suff = ShellColors.OFF if not self._disable_log_color else ''

        if self._inject_ts:
            pref += f'{datetime.now().strftime(self._ts_format)}  '

        if level:
            pref += f'[{level.value.value}]  '

        print(f'{pref}{msg}{suff}')
