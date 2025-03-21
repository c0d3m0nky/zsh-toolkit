from setuptools import setup, find_namespace_packages
from zsh_toolkit_py.shared.constants import zsh_toolkit_version

setup(
    name='zsh_toolkit_py',
    version=zsh_toolkit_version,
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    packages=find_namespace_packages(),
    py_modules=[
        # shared
        'zsh_toolkit_py.shared.file_utils', 'zsh_toolkit_py.shared.utils', 'zsh_toolkit_py.shared.magic_files', 'zsh_toolkit_py.shared.logger',
        'zsh_toolkit_py.shared.string_dbyte_utils', 'zsh_toolkit_py.shared.cli_args',
        # models
        'zsh_toolkit_py.models.disk_usage', 'zsh_toolkit_py.models.dockur',
        # tools
        'zsh_toolkit_py.tools.update', 'zsh_toolkit_py.tools.flatten', 'zsh_toolkit_py.tools.rxmv', 'zsh_toolkit_py.tools.decomp',
        'zsh_toolkit_py.tools.disk_usage', 'zsh_toolkit_py.tools.little_guys', 'zsh_toolkit_py.tools.dockur', 'zsh_toolkit_py.tools.replace_double_byte_chars',
        'zsh_toolkit_py.tools.git_auto_commit', 'zsh_toolkit_py.tools.disorder', 'zsh_toolkit_py.tools.group_files'
    ],
    entry_points={
        'console_scripts': [
            '_ztk-update=zsh_toolkit_py.tools.update:main',
            'flatten=zsh_toolkit_py.tools.flatten:main',
            'rxmv=zsh_toolkit_py.tools.rxmv:main',
            'folderDensity=zsh_toolkit_py.tools.folder_density:main',
            'decomp=zsh_toolkit_py.tools.decomp:main',
            'duh=zsh_toolkit_py.tools.disk_usage:main',
            'fack=zsh_toolkit_py.tools.little_guys:fack',
            'repdb=zsh_toolkit_py.tools.replace_double_byte_chars:main',
            'git_auto_commit=zsh_toolkit_py.tools.git_auto_commit:main',
            'random=zsh_toolkit_py.tools.disorder:_main',
            'group=zsh_toolkit_py.tools.group_files:main'
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
