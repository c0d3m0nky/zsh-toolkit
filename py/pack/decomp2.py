import re
import shutil
from dataclasses import dataclass
from typing import Callable, Any, Dict, Union, List, Tuple

from pathlib import Path
from zipfile import ZipFile, ZipInfo
import tempfile

from cli_args import BaseTap, PathArg
from py.pack.utils import first

_warned = False

_feat_sevz = False

# noinspection PyBroadException
try:
    from py7zr import SevenZipFile
    from py7zr.py7zr import ArchiveFile as SevZipArchiveFile

    _feat_sevz = True
except:
    _warned = True
    SevenZipFile = Any
    print('WARN: 7z unsupported by system')

_feat_rar = False

# noinspection PyBroadException
try:
    from unrar.cffi import rarfile, RarFile, RarInfo

    _feat_rar = True
except:
    _warned = True
    RarFile = Any
    print('WARN: rar unsupported by system')

if _warned:
    print('')


@dataclass
class CreateRootFolderResult:
    create: bool
    is_single: bool
    root_name: str


class ContextWrapper:
    archive: Union[RarFile]

    def __init__(self, archive):
        self.archive = archive

    def __enter__(self):
        return self.archive

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


ArchiveFileInfo = Union[ZipFile, SevenZipFile, RarFile, ContextWrapper]
CreateRootFolder = Callable[[List[ArchiveFileInfo]], CreateRootFolderResult]
DeflateArchive = Callable[[ArchiveFileInfo, Path], None]
OpenArchive = Callable[[Path], ArchiveFileInfo]


class Args(BaseTap):
    root: Path = Path('./')
    glob: str = '*.*'
    output: Path = Path('./')
    force_root: bool = False

    def configure(self) -> None:
        self.description = 'Bulk decompress archive files'
        self.add_root_optional('Directory to search for archives')
        self.add_optional('-g', '--glob', help="File glob to iterate over", default='*.*')
        self.add_optional('-o', '--output', type=PathArg, help='Directory to extract archives to', default='./')
        self.add_flag("-fr", "--force-root", help="Extract to root named after archive")

    def print_help(self, file=None):
        BaseTap.print_help(self, file=file)
        msg = ''

        if not _feat_sevz:
            msg += '7z unsupported by system\n'

        if not _feat_rar:
            msg += 'rar unsupported by system\n'

        msg = msg.strip('\n')

        if msg:
            print(f'\n{msg}')


@dataclass
class LibFuncs:
    create_root_folder: CreateRootFolder
    deflate: DeflateArchive
    open: OpenArchive


def sevz_create_root_folder(archive_files: List[SevenZipFile]) -> CreateRootFolderResult:
    # noinspection DuplicatedCode
    items: List[SevZipArchiveFile] = []
    file_names: List[str] = []

    for af in archive_files:
        for afi in af.files:
            if afi.filename not in file_names:
                file_names.append(afi.filename)
                items.append(afi)

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


def zip_create_root_folder(archive_files: List[ZipFile]) -> CreateRootFolderResult:
    # noinspection DuplicatedCode
    items: List[ZipInfo] = []
    file_names: List[str] = []

    for af in archive_files:
        for afi in af.filelist:
            if afi.filename not in file_names:
                file_names.append(afi.filename)
                items.append(afi)

    if len(items) == 0:
        raise 'Archive has no files'

    if len(items) == 1:
        return CreateRootFolderResult(False, True, items[0].filename)

    roots = []

    for li in items:
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


def rar_create_root_folder(archive_files: List[RarFile]) -> CreateRootFolderResult:
    items: List[RarInfo] = []
    file_names: List[str] = []

    for af in archive_files:
        for afi in af.infolist():
            if afi.filename not in file_names:
                file_names.append(afi.filename)
                items.append(afi)

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


def rar_deflate(archive: RarFile, op: Path) -> None:
    if not op.exists():
        op.mkdir(parents=True)

    for ai in archive.infolist():
        if not ai.is_dir():
            fop = op / ai.filename
            if not fop.parent.exists():
                fop.parent.mkdir(parents=True)
            with fop.open('w+b') as f:
                f.write(archive.read(ai))


@dataclass
class ArchiveFile:
    file: Path
    info: ArchiveFileInfo


class Archive:
    _create_root_folder_result: Union[CreateRootFolderResult, None] = None
    _files_initialized: bool = False
    files: List[ArchiveFile]
    lib: LibFuncs
    friendly_name: str

    def __init__(self, files: List[Path], lib: LibFuncs, friendly_name: str) -> None:
        self.files = [ArchiveFile(f, lib.open(f)) for f in files]
        self.lib = lib
        self.friendly_name = friendly_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        for af in self.files:
            af.info.__exit__(exc_type, exc_value, exc_tb)

    def _initialize_files(self):
        if not self._files_initialized:
            for af in self.files:
                af.info.__enter__()

    def _lazy_load_create_root_folder_result(self):
        self._initialize_files()

        if self._create_root_folder_result is None:
            self._create_root_folder_result = self.lib.create_root_folder(self.files)

    @property
    def is_multi_part(self) -> bool:
        return len(self.files) > 1

    @property
    def create_root_folder(self) -> bool:
        self._lazy_load_create_root_folder_result()

        return self._create_root_folder_result.create

    @property
    def is_single_file(self) -> bool:
        self._lazy_load_create_root_folder_result()

        return self._create_root_folder_result.is_single

    @property
    def root_name(self) -> str:
        self._lazy_load_create_root_folder_result()

        return self._create_root_folder_result.root_name


_libs: Dict[str, LibFuncs] = {
    'zip': LibFuncs(zip_create_root_folder, lambda a, o: a.extractall(o), lambda f: ZipFile(f))
}

if _feat_sevz:
    _libs['7z'] = LibFuncs(sevz_create_root_folder, lambda a, o: a.extractall(o), lambda f: SevenZipFile(f, mode='r'))

if _feat_rar:
    _libs['rar'] = LibFuncs(rar_create_root_folder, rar_deflate, lambda f: ContextWrapper(RarFile(f)))

_args = Args().parse_args()


def get_friendly_name(path: Path, root: Path) -> str:
    fn = path.relative_to(root).as_posix()

    if fn == path.name:
        fn = f'./{fn}'

    return fn


_rx_multiparts: List[re.Pattern] = [
    re.compile(r'^(.+)[._-]part(\d+)$', re.IGNORECASE)
]


def get_archives(root: Path) -> List[Archive]:
    if root.is_file():
        files = [root]
        root = root.parent
    else:
        files = [f for f in root.glob(_args.glob) if f.is_file()]

    lib_files: Dict[str, List[Path]] = {}

    for f in files:
        if f.suffix.strip('.') in _libs:
            lib_key = f.suffix.strip('.')

            if lib_key not in lib_files:
                lib_files[lib_key] = []

            lib_files[lib_key].append(f)

    res: List[Archive] = []

    for lib_key, files in lib_files.items():
        multipart_archives: Dict[str, List[Tuple[int, Path]]] = {}

        for f in files:
            m = first([m for m in [rx.search(f.stem) for rx in _rx_multiparts] if m])

            if m:
                short_name = m.group(1)
                part = m.group(2)

                if short_name not in multipart_archives:
                    multipart_archives[short_name] = []

                multipart_archives[short_name].append((part, f))
            else:
                res.append(Archive([f], _libs[lib_key], get_friendly_name(root, f)))

        for mk, m_parts in multipart_archives.items():
            friendly_name = get_friendly_name(root, files[0].parent / mk)
            mp_indexes = [p[0] for p in m_parts]
            mp_len = len(m_parts)
            mp_min = min(mp_indexes)
            mp_max = max(mp_indexes)
            mp_complete = False

            if mp_min == 0:
                mp_complete = (mp_max + 1 - mp_len) == 0
            elif mp_min == 1:
                mp_complete = (mp_max - mp_len) == 0

            if mp_complete:
                files = [p[1] for p in m_parts]
                res.append(Archive(files, _libs[lib_key], friendly_name))
            else:
                print(f'Incomplete parts: {friendly_name}')

    return res


def main() -> None:
    archive_cnt: int = 0
    root = _args.root.resolve()
    output = _args.output.resolve()

    for aa in get_archives(root):
        archive_cnt += 1

        if aa.is_multi_part:
            print(f'Cannot support multiparts: {aa.friendly_name}')

        else:
            # Todo: this is a hack til multipart is supported
            af = aa.files[0]

            with af.info as afi:
                print(f'Processing {aa.friendly_name}')
                op = Path(output)
                temp_op = None

                # ToDo: When single root, ask if want renamed
                if _args.force_root or aa.create_root_folder:
                    nop = op / af.file.name.replace(af.file.suffix, '')
                    nopi = 0

                    while nop.exists():
                        nopi += 1
                        nop = op / f'{af.file.name} - {nopi}'

                    op = nop
                elif aa.is_single_file:
                    nf = Path(aa.root_name)
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
                elif aa.root_name:
                    nop = op / aa.root_name

                    if nop.exists():
                        nopi = 0

                        while nop.exists():
                            nopi += 1
                            nop = op / f'{aa.root_name} - {nopi}'

                        op = nop
                        temp_op = Path(tempfile.gettempdir()) / aa.root_name

                so = get_friendly_name(op, root)

                if not output.exists():
                    output.mkdir(parents=True)

                print(f'Decompressing {aa.friendly_name} to {so}')

                try:
                    if aa.is_single_file:
                        aa.lib.deflate(afi, temp_op)
                        shutil.move(temp_op / aa.root_name, op)
                    elif temp_op:
                        if temp_op.exists():
                            shutil.rmtree(temp_op)
                        aa.lib.deflate(afi, temp_op.parent)
                        shutil.move(temp_op, op)
                    else:
                        aa.lib.deflate(afi, op)
                except Exception as e:
                    print(f'Failed decompressing {aa.friendly_name}: {e}')

    if archive_cnt < 1:
        print('No supported archives found')


if __name__ == '__main__':
    main()
