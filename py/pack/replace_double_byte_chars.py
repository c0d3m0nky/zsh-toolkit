from pathlib import Path
from userinput import userinput

from utils import parse_bool
from cli_args import BaseTap
import string_utils


class Args(BaseTap):
    plan: bool = False

    def configure(self) -> None:
        self.description = 'Replace double byte chars in file & folder names'
        self.add_plan("Don't commit renames")


_args: Args


def rel_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def main():
    global _args
    _args = Args().parse_args()
    root = Path('./').resolve()

    for fso in root.iterdir():
        repl = string_utils.replace_dbl_byte_chars(fso.name)

        if repl.clean != fso.name:
            nf = fso.parent / repl.clean

            if nf.exists():
                print(f'{rel_path(root, nf)} exists')
            else:
                resp = parse_bool(userinput('', label=f'Rename file? {repl.highlighted}', cache=False), [None])

                if resp:
                    if _args.plan:
                        print(f'{rel_path(root, fso)} -> {rel_path(root, nf)}')
                    else:
                        fso.rename(nf)


if __name__ == '__main__':
    main()
