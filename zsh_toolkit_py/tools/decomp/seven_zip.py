from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from py7zr import SevenZipFile
from py7zr.py7zr import ArchiveFile as SevZipArchiveFile

from zsh_toolkit_py.tools.decomp.models import Decomper


class SevenZipDecomper(Decomper[SevenZipFile, SevZipArchiveFile]):

    def __init__(self):
        super().__init__()

    def _get_file_name(self, item: SevZipArchiveFile) -> str:
        return item.filename

    def _is_dir(self, item: SevZipArchiveFile) -> bool:
        return item.is_directory

    # noinspection DuplicatedCode
    def _get_archive_structure(self, archive_files: List[SevenZipFile]) -> List[SevZipArchiveFile]:
        items: List[SevZipArchiveFile] = []
        file_names: List[str] = []

        for af in archive_files:
            for afi in af.files:
                if afi.filename not in file_names:
                    file_names.append(afi.filename)
                    items.append(afi)

        return items

    def deflate(self, archive: SevenZipFile, output: Path) -> None:
        archive.extractall(output)

    def open(self, path: Path) -> SevenZipFile:
        return SevenZipFile(path, mode='r')
