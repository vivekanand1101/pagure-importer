#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='pagure_importer',
    packages=['pagure_importer'],
    version='0.0.2',
    description='CLI tool for imports to Pagure',
    author='Vivek Anand',
    author_email='vivekanand1101@gmail.com',
    url='https://pagure.io/pagure-importer',
    keywords=['pagure', 'importer', 'import'],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',

    ],
    license='GNU General Public License v2.0',
    entry_points={
        'console_scripts': [
            'pgimport = pagure_importer.run:main'
        ],
    },
    include_package_data=True,
    install_requires=read('requirements.txt'),
)
