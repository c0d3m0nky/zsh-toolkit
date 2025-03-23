from pathlib import Path
from typing import List, Tuple
from zipfile import ZipFile, ZipInfo

from zsh_toolkit_py.tools.decomp.models import Decomper, CommonArchivePatterns


class ZipDecomper(Decomper[ZipFile, ZipInfo]):

    def __init__(self):
        super().__init__()
        self.rx_multiparts.append(CommonArchivePatterns.Multipart_Part_Num)

    def _get_file_name(self, item: ZipInfo) -> str:
        return item.filename

    def _is_dir(self, item: ZipInfo) -> bool:
        return item.is_dir()

    # noinspection DuplicatedCode
    def _get_archive_structure(self, archive_files: List[ZipFile]) -> List[ZipInfo]:
        items: List[ZipInfo] = []
        file_names: List[str] = []

        for af in archive_files:
            for afi in af.filelist:
                if afi.filename not in file_names:
                    file_names.append(afi.filename)
                    items.append(afi)

        return items

    def deflate(self, archive: ZipFile, output: Path) -> None:
        archive.extractall(output)

    def open(self, path: Path) -> ZipFile:
        return ZipFile(path)
