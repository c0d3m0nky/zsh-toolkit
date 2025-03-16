import os
from dataclasses import dataclass


class HardwareInfo:
    code: str | None
    cpu_cores: int | None
    cpu_model: str

    def __init__(self, code=None, cpu_cores=None, cpu_model=None):
        self.code = code
        self.cpu_cores = cpu_cores
        self.cpu_model = cpu_model


class OsInfo:
    code: str | None
    pkg_mgr: str | None

    def __init__(self, code: str | None = None, pkg_mgr: str | None = None):
        self.code = code
        self.pkg_mgr = pkg_mgr


class SystemInfo:
    os: OsInfo
    hardware: HardwareInfo

    def __init__(self, os: OsInfo = OsInfo(), hardware: HardwareInfo = HardwareInfo()):
        self.os = os
        self.hardware = hardware


def marshal_system_info(d: dict) -> SystemInfo:
    keys = d.keys()
    if 'os' in keys and 'hardware' in keys:
        return SystemInfo(OsInfo(**d['os']), HardwareInfo(**d['hardware']))
    else:
        raise Exception(f'Invalid json data ({d.keys()})')
