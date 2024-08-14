from setuptools import setup
from constants import zsh_toolkit_version

setup(
    name='zsh_toolkit_py',
    version=zsh_toolkit_version,
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    py_modules=[
        'file_utils', 'utils', 'magic_files', 'logger', 'string_utils', 'cli_args',
        'update', 'flatten', 'rxmv', 'folder_density', 'decomp', 'disk_usage', 'little_guys', 'dockur', 'replace_double_byte_chars'
    ],
    entry_points={
        'console_scripts': [
            '_ztk-update=update:main',
            'flatten=flatten:main',
            'rxmv=rxmv:main',
            'folderDensity=folder_density:main',
            'decomp=decomp:main',
            'duh=disk_usage:main',
            'fack=little_guys:fack',
            'repdb=replace_double_byte_chars:main'
        ],
    },
    install_requires=[
        'typed-argument-parser',
        'python-rclone',
        'userinput',
        'numpy',
        'emoji',
        'GitPython',
        'tqdm',
        'py7zr',
        'unrar2-cffi',
        'docker',
        'PyYAML',
        'prettytable'
    ]
)
