from setuptools import setup

setup(
    name='flatten',
    version='1.0.4',
    description='Flattens directory structure',
    author='c0d3m0nky',
    entry_points={
        'console_scripts': ['flatten=flatten:main'],
    },
    install_requires=[
        'typed-argument-parser',
        'python-rclone',
        'userinput',
        'numpy',
        'emoji'
    ]
)
