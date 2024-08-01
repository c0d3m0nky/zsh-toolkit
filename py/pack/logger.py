import enum
import traceback
from datetime import datetime


class LogLevels(enum.Enum):
    ERROR = 'ERROR'
    LOG = 'LOG'
    TRACE = 'TRACE'


class Logger:
    _trace: bool
    _inject_ts: bool
    _ts_format: str

    def __init__(self, trace: bool = False, inject_date: bool = True, ts_format: str = '%Y-%m-%d %H:%M:%S'):
        self._trace = trace
        self._inject_ts = inject_date
        self._ts_format = ts_format

    def error(self, msg: str, exc: Exception = None) -> None:
        if exc:
            msg += f'\n{exc}'
            if self._trace:
                msg += f'\n{traceback.format_exc()}'

        self.log(msg, LogLevels.ERROR)

    def trace(self, msg: str) -> None:
        if self._trace:
            self.log(msg, LogLevels.TRACE)

    def log(self, msg: str, level: LogLevels = 'LOG') -> None:
        pref = datetime.now().strftime(self._ts_format) if self._inject_ts else ''

        if level:
            pref += f'  [{level}]'

        if pref:
            pref += '  '

        print(f'{pref}{msg}')
