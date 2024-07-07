from setuptools import setup

setup(
    name='zsh_toolkit_py',
    version='1.1.2',
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    entry_points={
        'console_scripts': [
            'flatten=flatten:main',
            'rxmv=rxmv:main',
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
