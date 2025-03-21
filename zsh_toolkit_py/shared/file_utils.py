import platform
from enum import Enum
from pathlib import Path
import hashlib


def get_file_hash(file_path: Path) -> str:
    return hashlib.md5(file_path.read_text().encode('utf-8')).hexdigest()


class TextFileContent:
    def __init__(self, file_path: Path):
        self.text = file_path.read_text()
        self.hash = hashlib.md5(self.text.encode('utf-8')).hexdigest()


class CaseSensitiveFileSystemTestResult(Enum):
    NotADir = 'file_path argument is not a directory'
    NotWritable = 'file_path is not writable'
    CaseSensitive = 'CaseSensitive'
    CaseInsensitive = 'CaseInsensitive'


def fs_case_sensitive(file_path: Path) -> CaseSensitiveFileSystemTestResult:
    if platform.system() == 'Windows':
        return CaseSensitiveFileSystemTestResult.CaseInsensitive
    else:
        # ToDo: add mount detection to avoid brute force test
        file_path = file_path.expanduser().resolve()

        if not file_path.is_dir():
            return CaseSensitiveFileSystemTestResult.NotADir

        test_file_name = '.cst'

        f1 = file_path / test_file_name
        f2 = file_path / test_file_name.upper()

        def clean():
            f1.unlink(missing_ok=True)
            f2.unlink(missing_ok=True)

        # noinspection PyBroadException
        try:
            f1.touch()
        except Exception:
            clean()
            return CaseSensitiveFileSystemTestResult.NotWritable

        # noinspection PyBroadException
        try:
            f2.touch()
        except Exception:
            clean()
            return CaseSensitiveFileSystemTestResult.NotWritable

        files = [f.name.lower() for f in file_path.glob('.*') if f.name.lower() == test_file_name]

        clean()

        return CaseSensitiveFileSystemTestResult.CaseInsensitive if len(files) == 1 else CaseSensitiveFileSystemTestResult.CaseSensitive
