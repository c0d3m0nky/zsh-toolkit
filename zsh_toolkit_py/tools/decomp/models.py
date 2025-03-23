from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, TypeVar, Generic, Union, Tuple, re


@dataclass
class CreateRootFolderResult:
    create: bool
    is_single: bool
    root_name: str


T_Archive = TypeVar('T_Archive')
T_ArchiveItem = TypeVar('T_ArchiveItem')


class DisposableWrapper[T_Archive]:
    archive: T_Archive

    def __init__(self, archive):
        self.archive = archive

    def __enter__(self) -> T_Archive:
        return self.archive

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


class CommonArchivePatterns(Enum):
    Multipart_Part_Num = re.compile(r'^(.+)[._-]part(\d+)$', re.IGNORECASE)


class Decomper[T_Archive, T_ArchiveItem]:
    rx_multiparts: List[re.Pattern]

    def __init__(self):
        self.rx_multiparts = []

    def _get_file_name(self, item: T_ArchiveItem) -> str:
        pass

    def _is_dir(self, item: T_ArchiveItem) -> bool:
        pass

    def _get_archive_structure(self, archive_files: List[T_Archive]) -> List[T_ArchiveItem]:
        pass

    def create_root_folder(self, archive_files: List[T_Archive]) -> CreateRootFolderResult:
        items = self._get_archive_structure(archive_files)

        if len(items) == 0:
            raise 'Archive has no files'

        if len(items) == 1:
            return CreateRootFolderResult(False, True, items[0].filename)

        files = []
        roots = []

        for item in items:
            if not self._is_dir(item):
                fp = Path(self._get_file_name(item))

                if len(fp.parts) > 1:
                    rn = fp.parts[0]
                else:
                    rn = '.'

                if rn not in roots:
                    roots.append(rn)

        if len(files) == 0:
            raise 'Archive has no files'

        if len(files) == 1:
            # ToDo: I only had this in rar, hmmmmm
            return CreateRootFolderResult(False, True, files[0].filename)

        is_single_root = (len(roots) == 1 and roots[0] != '.')

        return CreateRootFolderResult(not is_single_root, False, roots[0] if is_single_root else '')

    def deflate(self, archive: T_Archive, output: Path) -> None:
        pass

    def open(self, path: Path) -> T_Archive | DisposableWrapper:
        pass


@dataclass
class ArchiveFile[T_Archive]:
    file: Path
    info: T_Archive
