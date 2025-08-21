from pathlib import Path

from decomp_models import ArchiveHandler, Tags


class ZipHandler(ArchiveHandler):

    def __init__(self):
        super().__init__()
        self.tag: Tags = Tags.Zip

    def can_handle(self, file: Path) -> bool:
        return file.suffix.lower() == '.zip'
