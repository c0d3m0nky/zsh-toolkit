import re
import shutil
from typing import Any, Dict, Union, List, Tuple

from pathlib import Path
import tempfile

from zsh_toolkit_py.shared.cli_args import BaseTap, PathArg
from zsh_toolkit_py.shared.utils import first
from zsh_toolkit_py.tools.decomp.models import ArchiveFile, Decomper, CreateRootFolderResult
from zsh_toolkit_py.tools.decomp.zip import ZipDecomper

_warned = False
_feat_sevz = False

# noinspection PyBroadException
try:
    from zsh_toolkit_py.tools.decomp.seven_zip import SevenZipDecomper

    _feat_sevz = True
except:
    _warned = True
    SevenZipFile = Any
    print('WARN: 7z unsupported by system')

_feat_rar = False

# noinspection PyBroadException
try:
    from zsh_toolkit_py.tools.decomp.rar import RarDecomper

    _feat_rar = True
except:
    _warned = True
    RarFile = Any
    print('WARN: rar unsupported by system')

if _warned:
    print('')


class Args(BaseTap):
    root: Path = Path('../')
    glob: str = '*.*'
    output: Path = Path('../')
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


class Archive:
    _create_root_folder_result: Union[CreateRootFolderResult, None] = None
    _files_initialized: bool = False
    files: List[ArchiveFile]
    lib: Decomper
    friendly_name: str

    def __init__(self, files: List[Path], lib: Decomper, friendly_name: str) -> None:
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


_libs: Dict[str, Decomper] = {
    'zip': ZipDecomper()
}

if _feat_sevz:
    _libs['7z'] = SevenZipDecomper()

if _feat_rar:
    _libs['rar'] = RarDecomper()

_args = Args().parse_args()


def get_friendly_name(path: Path, root: Path) -> str:
    fn = path.relative_to(root).as_posix()

    if fn == path.name:
        fn = f'./{fn}'

    return fn


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
        decomper = _libs[lib_key]
        multipart_archives: Dict[str, List[Tuple[int, Path]]] = {}

        for f in files:
            m = first([m for m in [rx.search(f.stem) for rx in decomper.rx_multiparts] if m])

            if m:
                short_name = m.group(1)
                part = m.group(2)

                if short_name not in multipart_archives:
                    multipart_archives[short_name] = []

                multipart_archives[short_name].append((part, f))
            else:
                res.append(Archive([f], decomper, get_friendly_name(root, f)))

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
