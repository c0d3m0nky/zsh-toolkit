from dataclasses import dataclass
from typing import Callable, Any, Dict

from tap import Tap
from pathlib import Path
from zipfile import ZipFile
from py7zr import SevenZipFile
from unrar import rarfile

from utils import arg_to_path

CreateRootFolder = Callable[[Any], bool]
DeflateArchive = Callable[[Any, Path], None]
OpenArchive = Callable[[Path], Any]


class Args(Tap):
    root: Path = Path('./')
    glob: str = '*.*'
    output: Path = Path('./')

    def configure(self) -> None:
        self.description = 'Bulk decompress archive files'
        self.add_argument('root', type=arg_to_path, nargs='?', help='Directory to search for archives', default='./')
        self.add_argument('-g', '--glob', help="File glob to iterate over", default='*.*', required=False)
        self.add_argument('-o', '--output', type=arg_to_path, help='Directory to extract archives to', default='./', required=False)


@dataclass
class LibFuncs:
    create_root_folder: CreateRootFolder
    deflate: DeflateArchive
    open: OpenArchive


def sevz_create_root_folder(archive: SevenZipFile) -> bool:
    print('Stub sevz_create_root_folder')
    return True


def sevz_deflate(archive: SevenZipFile, output: Path) -> None:
    print('Stub sevz_deflate')
    return


def sevz_open(file: Path) -> SevenZipFile:
    return SevenZipFile(file.as_posix(), mode='r')


def zip_create_root_folder(archive: ZipFile) -> bool:
    print('Stub zip_create_root_folder')
    return True


def zip_deflate(archive: SevenZipFile, output: Path) -> None:
    print('Stub zip_deflate')
    return


def zip_open(file: Path) -> ZipFile:
    return ZipFile(file.as_posix())


def rar_create_root_folder(archive: rarfile.RarFile) -> bool:
    print('Stub rar_create_root_folder')
    return True


def rar_deflate(archive: rarfile.RarFile, output: Path) -> None:
    print('Stub rar_deflate')
    return


def rar_open(file: Path) -> rarfile.RarFile:
    return rarfile.RarFile(file.as_posix())


_libs: Dict[str, LibFuncs] = {
    '7z': LibFuncs(sevz_create_root_folder, sevz_deflate, sevz_open),
    'zip': LibFuncs(zip_create_root_folder, zip_deflate, zip_open),
    'rar': LibFuncs(rar_create_root_folder, rar_deflate, rar_open)
}

_args = Args().parse_args()


def friendly_name(path: Path, root: Path) -> str:
    fn = path.relative_to(root).as_posix()

    if fn == path.name:
        fn = f'./{fn}'

    return fn


acnt: int = 0
root = _args.root.resolve()
output = _args.output.resolve()

for f in root.glob(_args.glob):
    if f.is_file() and f.suffix.strip('.') in _libs:
        acnt += 1
        lib = _libs[f.suffix.strip('.')]

        with lib.open(f) as a:
            op = Path(output)

            if lib.create_root_folder(a):
                dname = f.name.replace(f.suffix, '')
                nop = op / dname
                nopi = 0

                while nop.exists():
                    nopi += 1
                    nop = op / f'{dname} - {nopi}'

                op = nop

            sf = friendly_name(f, root)
            so = friendly_name(op, root)
            print(f'Decompressing {sf} to {so}')

            try:
                lib.deflate(a, op)
            except Exception as e:
                print(f'Failed decompressing {sf}: {e}')

if acnt < 1:
    print('No supported archives found')
