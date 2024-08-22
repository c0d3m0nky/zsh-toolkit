from pathlib import Path
from typing import List, Iterator, Dict, Self, Union, Callable

from utils import ShellColors, is_in


class Stat:
    name: str

    def __init__(self, name: str):
        self.name = name

    @property
    def has_errors(self) -> bool:
        raise NotImplementedError

    @property
    def size(self) -> int:
        raise NotImplementedError

    @property
    def file_count(self) -> int:
        raise NotImplementedError

    @property
    def density(self) -> int:
        if self.file_count == 0 or self.size <= 0:
            return 0

        return round(self.size / self.file_count)

    @property
    def max_size(self) -> int:
        raise NotImplementedError


class BareStat(Stat):
    _has_errors: bool
    _size: int
    _file_count: int
    _max_size: int

    def __init__(self, name: str):
        super().__init__(name)
        self._size = 0
        self._file_count = 0
        self._max_size = 0
        self._has_errors = False

    @property
    def has_errors(self) -> bool:
        return self._has_errors

    @property
    def size(self) -> int:
        return self._size

    @property
    def file_count(self) -> int:
        return self._file_count

    @property
    def density(self) -> int:
        if self.file_count == 0 or self.size <= 0:
            return 0

        return round(self.size / self.file_count)

    @property
    def max_size(self) -> int:
        return self._max_size


class Dir(Stat):
    _density: Union[int, None] = None
    _has_errors: bool
    name: str
    sizes: List[int]

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name
        self.sizes = []
        self._has_errors = False

    @property
    def size(self) -> int:
        return sum(self.sizes)

    @property
    def file_count(self):
        return len(self.sizes)

    @property
    def max_size(self) -> int:
        return max(self.sizes) if self.sizes else 0

    @property
    def has_errors(self) -> bool:
        return self._has_errors

    def had_error(self, he: bool) -> None:
        self._has_errors = self._has_errors or he


class State:
    _errors: Dict[str, List[Path]]
    _dirs: List[Stat]
    _root: Path
    name: str
    total_stat: BareStat
    root_stat: BareStat

    def __init__(self, root: Path, root_stat: BareStat, total_stat: BareStat) -> None:
        self._root = root
        self.name = root.name
        self._errors = {}
        self._dirs = []
        self.total_stat = total_stat
        self.root_stat = root_stat

    def task_state(self, base: Path) -> Self:
        return State(base, BareStat(self.root_stat.name), BareStat(self.total_stat.name))

    @property
    def dirs(self) -> Iterator[Stat]:
        return iter(self._dirs)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def has_errors(self) -> bool:
        return bool(self._errors.keys())

    # noinspection PyShadowingBuiltins, PyProtectedMember
    def add_dir(self, dir: Stat) -> None:
        self._dirs.append(dir)

        self.total_stat._size += dir.size
        self.total_stat._file_count += dir.file_count
        dmx = dir.max_size

        if dmx > self.total_stat.max_size:
            self.total_stat._max_size = dmx

    # noinspection PyProtectedMember
    def add_to_root(self, size: int, has_errors: bool) -> None:
        self.root_stat._size += size
        self.root_stat._file_count += 1
        self.root_stat._has_errors = self.root_stat.has_errors or has_errors

        if size > self.root_stat.max_size:
            self.root_stat._max_size = size

    def calculate(self) -> None:
        pass

    def error(self, key: str, path: Path) -> None:
        if key not in self._errors:
            self._errors[key] = []

        self._errors[key].append(path)

    def get_relative_path(self, path: Path) -> str:
        return path.relative_to(self._root).as_posix()

    def get_errors(self) -> Dict[str, List[str]]:
        return {k: [self.get_relative_path(p) for p in v] for k, v in self._errors.items()}

    # noinspection PyProtectedMember
    def merge(self, state: Self) -> None:
        for k in state._errors.keys():
            for path in state._errors[k]:
                self.error(k, path)

        for d in state._dirs:
            self.add_dir(d)

        self.root_stat._size += state.root_stat.size

        if state.root_stat.max_size > self.root_stat.max_size:
            self.root_stat._max_size = state.root_stat.max_size

        self.root_stat._file_count += state.root_stat.file_count

        if state.root_stat.max_size > self.total_stat.max_size:
            self.total_stat._max_size = state.root_stat.max_size


# region Grid classes

class Field:
    name: str
    alignment: str
    get_value: Callable[[Self, Stat], str]
    width: int
    color: Union[ShellColors, None]

    def __init__(self, name: str, alignment: str, get_value: Callable[[Self, Stat], str], width: int, color: Union[ShellColors, None] = None) -> None:
        self.name = name
        self.alignment = alignment
        self.get_value = get_value
        self.width = width
        self.color = color


class Grid:
    _field_left_padding_width: int = 0
    _field_right_padding_width: int = 2
    _left_padding: int = 1
    _right_padding: int = 0
    _int_field_padding = 1
    _fields: List[Field] = []

    additional_fields: Dict[str, Field]
    max_name_len: int
    max_width: int

    def __init__(self, max_width: int, max_name_len: int) -> None:
        self.max_width = max_width
        self.max_name_len = max_name_len
        self.additional_fields = {}

    @property
    def field_padding(self) -> int:
        return self._field_left_padding_width + self._field_right_padding_width

    @property
    def field_left_padding_width(self) -> int:
        return self._field_left_padding_width

    @property
    def field_right_padding_width(self) -> int:
        return self._field_right_padding_width

    @property
    def int_field_padding(self) -> int:
        return self._int_field_padding

    @property
    def fields(self) -> Iterator[Field]:
        return iter(self._fields)

    def add_field(self, field: Field) -> None:
        if not is_in(field, self._fields, lambda a, b: a.name == b.name):
            self._fields.append(field)

    def remove_last_field(self) -> None:
        _ = self._fields.pop()

    def can_fit_field(self, field: Field, buffer: int = 0) -> bool:
        return self.remaining_width(buffer) > field.width + self.field_padding

    def remaining_width(self, buffer: int = 0) -> int:
        return self.max_width - self._left_padding - sum([f.width + self.field_padding for f in self.fields]) - buffer - self._right_padding

# endregion
