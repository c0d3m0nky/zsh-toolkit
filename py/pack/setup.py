from setuptools import setup

setup(
    name='zsh_toolkit_py',
    version='1.1.3',
    description='ZSH utils I find useful',
    author='c0d3m0nky',
    py_modules=['flatten','rxmv'],
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
