from pathlib import Path
from typing import Dict


class Pkg:
    id: str
    fields: Dict[str, str]
    pipx: str | None
    pipx_local: Path | None
    os: str | None
    which: str | None
    required: bool

    def __init__(self, pkg_id: str, fields: Dict[str, str], base_path: Path) -> None:
        self.id = pkg_id
        self.required = fields['required'] if 'required' in fields else False
        self.os = fields['os'] if 'os' in fields else None
        self.pipx = fields['pipx'] if 'pipx' in fields else None
        pipx_local = fields['pipx_local'] if 'pipx_local' in fields else None
        self.which = fields['which'] if 'which' in fields else None

        if pipx_local:
            if pipx_local.startswith('.'):
                self.pipx_local = (base_path / pipx_local)
            else:
                self.pipx_local = Path(pipx_local)

            self.pipx_local = self.pipx_local.expanduser().resolve()
        else:
            self.pipx_local = None

        if 'required' in fields:
            fields.pop('required')
        if 'which' in fields:
            fields.pop('which')

        self.fields = fields

    def details(self, pkgman: str) -> str:
        op = []

        if self.pipx_local:
            op.append(f'pipx_local: {self.pipx_local}')
        if self.pipx:
            op.append(f'pipx: {self.pipx}')
        if pkgman and pkgman in self.fields:
            op.append(f'{pkgman}: {self.fields[pkgman]}')
        elif self.os:
            op.append(f'{pkgman}: {self.os}')

        return '\t'.join(op)


class InitData:
    pkg: Dict[str, Pkg] = {}

    def __init__(self, data: Dict[str, Dict[str, Dict[str, str]]], base_path: Path) -> None:
        pkg = data['pkg']
        for pk in pkg:
            self.pkg[pk] = Pkg(pk, pkg[pk], base_path)
