from setuptools import setup
from constants import zsh_toolkit_version

setup(
    name='zsh_toolkit_py',
    version=zsh_toolkit_version,
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    py_modules=[
        'file_utils', 'utils', 'magic_files',
        'update', 'flatten', 'rxmv', 'folder_density', 'decomp', 'disk_usage', 'little_guys', 'dockur'
    ],
    entry_points={
        'console_scripts': [
            '_ztk-update=update:main',
            'flatten=flatten:main',
            'rxmv=rxmv:main',
            'folderDensity=folder_density:main',
            'decomp=decomp:main',
            'duh=disk_usage:main',
            'fack=little_guys:fack'
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
        'PyYAML'
    ]
)
