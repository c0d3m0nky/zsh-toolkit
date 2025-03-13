from typing import Dict


class Pkg:
    id: str
    fields: Dict[str, str]
    pipx: str
    pipx_local: str
    os: str
    which: str
    required: bool

    # noinspection PyShadowingNames
    def __init__(self, id: str, fields: Dict[str, str]) -> None:
        self.id = id
        self.required = fields['required'] if 'required' in fields else False
        self.os = fields['os'] if 'os' in fields else None
        self.pipx = fields['pipx'] if 'pipx' in fields else None
        self.pipx_local = fields['pipx_local'] if 'pipx_local' in fields else None
        self.which = fields['which'] if 'which' in fields else None

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

    def __init__(self, pkg: Dict[str, Dict[str, str]] = None) -> None:
        for pk in pkg:
            self.pkg[pk] = Pkg(pk, pkg[pk])
