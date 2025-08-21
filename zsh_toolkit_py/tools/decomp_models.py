from dataclasses import dataclass
from pathlib import Path
from enum import Flag, auto
from typing import List

from zsh_toolkit_py.tools.decomp_zip import ZipHandler


class Tags(Flag):
    NONE = 0
    Zip = auto()
    Rar = auto()
    SevZ = auto()
    Split = auto()

@dataclass
class Candidate:
    path: Path
    tags: Tags


class Archive:
    files: List[Path]


class ArchiveHandler:

    def __init__(self):
        self.tag: Tags = Tags.NONE

    def can_handle(self, file: Path) -> bool:
        return False


archive_handlers: List[ArchiveHandler] = [
    ZipHandler
]