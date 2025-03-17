from pathlib import Path
import hashlib


def get_file_hash(file_path: Path) -> str:
    return hashlib.md5(file_path.read_text().encode('utf-8')).hexdigest()


class TextFileContent:
    def __init__(self, file_path: Path):
        self.text = file_path.read_text()
        self.hash = hashlib.md5(self.text.encode('utf-8')).hexdigest()
