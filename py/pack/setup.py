from setuptools import setup
from constants import zsh_toolkit_version

setup(
    name='zsh_toolkit_py',
    version=zsh_toolkit_version,
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    py_modules=[
        'file_utils', 'utils', 'magic_files', 'logger', 'string_dbyte_utils', 'cli_args', 'disk_usage_models',
        'update', 'flatten', 'rxmv', 'decomp', 'disk_usage', 'little_guys', 'dockur', 'replace_double_byte_chars',
        'git_auto_commit', 'disorder'
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
            'repdb=replace_double_byte_chars:main',
            'git_auto_commit=git_auto_commit:main',
            'random=disorder:_main'
        ],
    },
    install_requires=[
        'typed-argument-parser',
        'python-rclone',
        'numpy',
        'emoji',
        'GitPython',
        'tqdm',
        'py7zr',
        'unrar2-cffi',
        'docker',
        'PyYAML',
        'prettytable',
        'english-words'
    ]
)
