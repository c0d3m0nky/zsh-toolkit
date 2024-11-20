from pathlib import Path

from cli_args import BaseTap
from utils import Ask
import string_dbyte_utils

_ask = Ask()


class Args(BaseTap):
    remove_filler_chars: bool = False
    commit: bool = False
    plan: bool = False

    def configure(self) -> None:
        self.description = 'Replace double byte chars in file & folder names'
        self.add_flag('-f', '--remove-filler-chars', help='Don\'t ask, just do it')
        self.add_flag('-c', '--commit', help='Don\'t ask, just do it')
        self.add_plan("Don't commit renames")


_args: Args


def rel_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def main():
    global _args
    _args = Args().parse_args()
    root = Path('./').resolve()
    files = sorted(root.iterdir(), key=lambda f: f.name)

    for fso in files:
        repl = string_dbyte_utils.replace_dbl_byte_chars(fso.name)

        if _args.remove_filler_chars:
            repl = string_dbyte_utils.remove_consecutive_filler_chars(repl)

        if repl.clean != fso.name:
            nf = fso.parent / repl.clean

            if nf.exists():
                print(f'{rel_path(root, nf)} exists')
            else:
                resp = True if _args.commit else _ask.yes_no(f'Rename file? {repl.highlighted}', empty_is_true=True)

                if resp:
                    if _args.plan:
                        print(f'{rel_path(root, fso)} -> {rel_path(root, nf)}')
                    else:
                        fso.rename(nf)


if __name__ == '__main__':
    main()
