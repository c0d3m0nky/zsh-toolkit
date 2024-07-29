from setuptools import setup
from constants import zsh_toolkit_version

setup(
    name='zsh_toolkit_py',
    version=zsh_toolkit_version,
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    py_modules=['flatten', 'rxmv', 'update', 'folder_density', 'utils', 'decomp', 'disk_usage'],
    entry_points={
        'console_scripts': [
            'flatten=flatten:main',
            'rxmv=rxmv:main',
            'ztk-update=update:main',
            'folderDensity=folder_density:main',
            'decomp=decomp:main',
            'disk_usage=disk_usage:main'
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
        'unrar2-cffi'
    ]
)
