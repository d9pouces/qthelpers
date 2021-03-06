# coding=utf-8
import sys


__author__ = 'flanker'

"""Setup file for the QtExample project.
"""

import os.path

import ez_setup

ez_setup.use_setuptools()

try:
    from cx_Freeze import setup, Executable
except ImportError:
    from setuptools import setup, find_packages

    Executable = None

# get README content from README.rst file
with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as fd:
    long_description = fd.read()

# get version value from VERSION file
with open(os.path.join(os.path.dirname(__file__), 'VERSION'), encoding='utf-8') as fd:
    version = fd.read().strip()
entry_points = {'console_scripts': ['qtexample = qtexample.cli:main']}

kwargs = {}
if Executable is not None:
    base = 'Win32GUI' if sys.platform == 'win32' else None
    buildOptions = dict(packages=[], excludes=[])
    kwargs['options'] = dict(build_exe=buildOptions)
    kwargs['executables'] = [Executable('run.py', base=base)]

setup(
    name='qthelpers',
    version=version,
    description='No description yet.',
    long_description=long_description,
    author='flanker',
    author_email='flanker@19pouces.net',
    license='cecill_b',
    url='',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='qthelpers.tests',
    install_requires=['setuptools>=1.0', 'PySide', 'cx_Freeze'],
    setup_requires=['setuptools>=1.0'],
    classifiers=[],
    **kwargs
)