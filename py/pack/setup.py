from setuptools import setup
from constants import zsh_toolkit_version

setup(
    name='zsh_toolkit_py',
    version=zsh_toolkit_version,
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    py_modules=['flatten','rxmv','update'],
    entry_points={
        'console_scripts': [
            'flatten=flatten:main',
            'rxmv=rxmv:main',
            'zsh-toolkit-update=update:main'
        ],
    },
    install_requires=[
        'typed-argument-parser',
        'python-rclone',
        'userinput',
        'numpy',
        'emoji'
    ]
)
