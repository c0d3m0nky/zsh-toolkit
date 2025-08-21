from pathlib import Path
from typing import List

from zsh_toolkit_py.shared.cli_args import BaseTap, PathArg
from decomp_models import Tags, Candidate, Archive, archive_handlers


class Args(BaseTap):
    root: Path
    glob: str = '*.*'
    output: Path
    force_root: bool = False

    def configure(self) -> None:
        self.description = 'Bulk decompress archive files'
        self.add_root_optional('Directory to search for archives')
        self.add_optional('-g', '--glob', help="File glob to iterate over", default='*.*')
        self.add_optional('-o', '--output', type=PathArg, help='Directory to extract archives to', default='./')
        self.add_flag("-fr", "--force-root", help="Extract to root named after archive")


_args = Args().parse_args()


def main() -> None:
    archive_cnt: int = 0
    root = _args.root.expanduser().resolve()
    output = _args.output.expanduser().resolve()

    candidates: List[Candidate] = []

    for f in root.glob(_args.glob):
        tags: Tags = Tags.NONE

        for ah in archive_handlers:
            if ah.can_handle(f):
                tags = tags | ah.tag

        if tags != Tags.NONE:
            candidates.append(Candidate(f, tags))

    # resolve candidates


if __name__ == '__main__':
    main()
