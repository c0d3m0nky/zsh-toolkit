from pathlib import Path
from typing import List, Tuple

from unrar.cffi import RarFile, RarInfo

from zsh_toolkit_py.tools.decomp.models import Decomper, DisposableWrapper, CommonArchivePatterns


class RarDecomper(Decomper[RarFile, RarInfo]):

    def __init__(self):
        super().__init__()
        self.rx_multiparts.append(CommonArchivePatterns.Multipart_Part_Num)

    def _get_file_name(self, item: RarInfo) -> str:
        return item.filename

    def _is_dir(self, item: RarInfo) -> bool:
        return item.is_dir()

    def _get_archive_structure(self, archive_files: List[RarFile]) -> List[RarInfo]:
        items: List[RarInfo] = []
        file_names: List[str] = []

        for af in archive_files:
            for afi in af.infolist():
                if afi.filename not in file_names:
                    file_names.append(afi.filename)
                    items.append(afi)

        return items

    def deflate(self, archive: RarFile, output: Path) -> None:
        if not output.exists():
            output.mkdir(parents=True)

        for ai in archive.infolist():
            if not ai.is_dir():
                fop = output / ai.filename
                if not fop.parent.exists():
                    fop.parent.mkdir(parents=True)
                with fop.open('w+b') as f:
                    f.write(archive.read(ai))

    def open(self, path: Path) -> DisposableWrapper:
        return DisposableWrapper[RarFile](path)
