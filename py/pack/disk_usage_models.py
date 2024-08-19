from pathlib import Path
from typing import List, Iterator, Dict, Self, Union, Callable

from utils import ShellColors, is_in


class Dir:
    _density: Union[int, None] = None
    name: str
    size: int
    file_count: Union[int, None]
    has_errors: bool

    def __init__(self, name: str, size: int = 0, file_count: int = 0, has_errors: bool = False):
        self.name = name
        self.size = size
        self.file_count = file_count
        self.has_errors = has_errors

    @property
    def density(self) -> int:
        if self._density is None:
            self.recalculate()

        return self._density

    def recalculate(self) -> None:
        if self.file_count is None:
            self._density = None
            return
        elif self.file_count == 0 or self.size <= 0:
            self._density = 0
            return

        self._density = round(self.size / self.file_count)


class State:
    _errors: Dict[str, List[Path]]
    _dirs: List[Dir]
    _root: Path
    _total_size: int
    _total_file_count: int
    _root_size: int
    _root_file_count: int
    _root_has_errors: bool

    def __init__(self, root: Path) -> None:
        # These must be set here or multithreading won't serialize
        self._errors = {}
        self._dirs = []
        self._total_size = 0
        self._total_file_count = 0
        self._root_size = 0
        self._root_file_count = 0
        self._root = root
        self._root_has_errors = False

    @property
    def dirs(self) -> Iterator[Dir]:
        return iter(self._dirs)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def root_size(self) -> int:
        return self._root_size

    @property
    def root_file_count(self) -> int:
        return self._root_file_count

    @property
    def root_has_errors(self) -> bool:
        return self._root_has_errors

    @property
    def total_size(self) -> int:
        return self._total_size

    @property
    def total_file_count(self) -> int:
        return self._total_file_count

    @property
    def has_errors(self) -> bool:
        return bool(self._errors.keys())

    # noinspection PyShadowingBuiltins
    def add_dir(self, dir: Dir) -> None:
        self._dirs.append(dir)
        self._total_size += dir.size
        self._total_file_count += dir.file_count

    def add_to_root(self, size: int, file_count: int, has_errors: bool) -> None:
        self._root_size += size
        self._root_file_count += file_count
        self._total_size += size
        self._total_file_count += file_count
        self._root_has_errors = self._root_has_errors or has_errors

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

    def merge(self, state: Self) -> None:
        for k in state._errors.keys():
            for path in state._errors[k]:
                self.error(k, path)

        for d in state._dirs:
            self.add_dir(d)

        self._total_size += state.total_size
        self._total_file_count += state.total_file_count
        self._root_size += state.root_size
        self._root_file_count += state.root_file_count


# region Grid classes

class Field:
    name: str
    alignment: str
    get_value: Callable[[Self, Dir], str]
    width: int
    color: Union[ShellColors, None]

    def __init__(self, name: str, alignment: str, get_value: Callable[[Self, Dir], str], width: int, color: Union[ShellColors, None] = None) -> None:
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

    max_width: int

    def __init__(self, max_width: int):
        self.max_width = max_width

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

    def can_fit_field(self, field: Field, buffer: int = 0) -> bool:
        return self.remaining_width(buffer) > field.width + self.field_padding

    def remaining_width(self, buffer: int = 0) -> int:
        return self.max_width - self._left_padding - sum([f.width + self.field_padding for f in self.fields]) - buffer - self._right_padding


# endregion
