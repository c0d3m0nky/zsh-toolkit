import shutil
from dataclasses import dataclass
from typing import Callable, Any, Dict, Union, Tuple, List

from tap import Tap
from pathlib import Path
from zipfile import ZipFile
import tempfile

from utils import arg_to_path

_feat_sevz = False

try:
    from py7zr import SevenZipFile
    from py7zr.py7zr import ArchiveFile

    _feat_sevz = False
except Exception as e:
    print('WARN: 7z unsupported by system')

_feat_rar = False

try:
    from unrar.cffi import rarfile, RarInfo

    _feat_rar = False
except Exception as e:
    print('WARN: rar unsupported by system')


@dataclass
class CreateRootFolderResult:
    create: bool
    is_single: bool
    root_name: str


class ContextWrapper:

    def __init__(self, archive):
        self.archive = archive

    def __enter__(self):
        return self.archive

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


Archive = Union[ZipFile, SevenZipFile, rarfile.RarFile, ContextWrapper]
CreateRootFolder = Callable[[Archive], CreateRootFolderResult]
DeflateArchive = Callable[[Archive, Path], None]
OpenArchive = Callable[[Path], Archive]


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


def sevz_create_root_folder(archive: SevenZipFile) -> CreateRootFolderResult:
    items: List[ArchiveFile] = list(archive.files)

    if len(items) == 0:
        raise 'Archive has no files'

    if len(items) == 1:
        return CreateRootFolderResult(False, True, items[0].filename)

    roots = []

    for li in items:
        if not li.is_directory:
            fp = Path(li.filename)

            if len(fp.parts) > 1:
                rn = fp.parts[0]
            else:
                rn = '.'

            if rn not in roots:
                roots.append(rn)

    is_single_root = (len(roots) == 1 and roots[0] != '.')

    return CreateRootFolderResult(not is_single_root, False, roots[0] if is_single_root else '')


def sevz_deflate(archive: SevenZipFile, output: Path, path: Union[Path, None]) -> None:
    if path is None:
        archive.extractall(output)
    else:
        archive.extract(output, [path.as_posix()])


def zip_create_root_folder(archive: ZipFile) -> CreateRootFolderResult:
    if len(archive.filelist) == 0:
        raise 'Archive has no files'

    if len(archive.filelist) == 1:
        return CreateRootFolderResult(False, True, archive.filelist[0].filename)

    roots = []

    for li in archive.filelist:
        if not li.is_dir():
            fp = Path(li.filename)

            if len(fp.parts) > 1:
                rn = fp.parts[0]
            else:
                rn = '.'

            if rn not in roots:
                roots.append(rn)

    is_single_root = (len(roots) == 1 and roots[0] != '.')

    return CreateRootFolderResult(not is_single_root, False, roots[0] if is_single_root else '')


def rar_create_root_folder(archive: rarfile.RarFile) -> CreateRootFolderResult:
    items: List[RarInfo] = list(archive.infolist())

    if len(items) == 0:
        raise 'Archive has no files'

    files = []
    roots = []

    for li in items:
        if not li.is_dir():
            files.append(li)
            fp = Path(li.filename)

            if len(fp.parts) > 1:
                rn = fp.parts[0]
            else:
                rn = '.'

            if rn not in roots:
                roots.append(rn)

    if len(files) == 0:
        raise 'Archive has no files'

    if len(files) == 1:
        return CreateRootFolderResult(False, True, files[0].filename)

    is_single_root = (len(roots) == 1 and roots[0] != '.')

    return CreateRootFolderResult(not is_single_root, False, roots[0] if is_single_root else '')


def rar_deflate(archive: rarfile.RarFile, op: Path) -> None:
    if not op.exists():
        op.mkdir(parents=True)

    for ai in archive.infolist():
        if not ai.is_dir():
            fop = op / ai.filename
            if not fop.parent.exists():
                fop.parent.mkdir(parents=True)
            with fop.open('w+b') as f:
                f.write(archive.read(ai))


_libs: Dict[str, LibFuncs] = {
    'zip': LibFuncs(zip_create_root_folder, lambda a, o: a.extractall(o), lambda f: ZipFile(f))
}

if _feat_sevz:
    _libs['7z'] = LibFuncs(sevz_create_root_folder, lambda a, o: a.extractall(o), lambda f: SevenZipFile(f, mode='r'))

if _feat_rar:
    _libs['rar'] = LibFuncs(rar_create_root_folder, rar_deflate, lambda f: ContextWrapper(rarfile.RarFile(f)))

_args = Args().parse_args()


def friendly_name(path: Path, root: Path) -> str:
    fn = path.relative_to(root).as_posix()

    if fn == path.name:
        fn = f'./{fn}'

    return fn


def main() -> None:
    acnt: int = 0
    root = _args.root.resolve()
    output = _args.output.resolve()

    for f in root.glob(_args.glob):
        if f.is_file() and f.suffix.strip('.') in _libs:
            acnt += 1
            lib = _libs[f.suffix.strip('.')]
            sf = friendly_name(f, root)

            print(f'Processing {sf}')

            with lib.open(f) as a:
                op = Path(output)
                res = lib.create_root_folder(a)
                temp_op = None

                if res.create:
                    nop = op / f.name.replace(f.suffix, '')
                    nopi = 0

                    while nop.exists():
                        nopi += 1
                        nop = op / f'{f.name} - {nopi}'

                    op = nop
                elif res.is_single:
                    nf = Path(res.root_name)
                    nfn = nf.name.replace(nf.suffix, '')
                    nfs = nf.suffix
                    nop = op / nf.name

                    if nop.exists():
                        nopi = 0

                        while nop.exists():
                            nopi += 1
                            nop = op / f'{nfn} - {nopi}{nfs}'

                    op = nop
                    temp_op = Path(tempfile.gettempdir())
                elif res.root_name:
                    nop = op / res.root_name

                    if nop.exists():
                        nopi = 0

                        while nop.exists():
                            nopi += 1
                            nop = op / f'{res.root_name} - {nopi}'

                        op = nop
                        temp_op = Path(tempfile.gettempdir()) / res.root_name

                so = friendly_name(op, root)

                if not output.exists():
                    output.mkdir(parents=True)

                print(f'Decompressing {sf} to {so}')

                try:
                    if res.is_single:
                        lib.deflate(a, temp_op)
                        shutil.move(temp_op / res.root_name, op)
                    elif temp_op:
                        if temp_op.exists():
                            shutil.rmtree(temp_op)
                        lib.deflate(a, temp_op.parent)
                        shutil.move(temp_op, op)
                    else:
                        lib.deflate(a, op)
                except Exception as e:
                    print(f'Failed decompressing {sf}: {e}')

    if acnt < 1:
        print('No supported archives found')


if __name__ == '__main__':
    main()
