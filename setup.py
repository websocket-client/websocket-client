"""

"""

"""
websocket - WebSocket client library for Python

Copyright (C) 2010 Hiroki Ohtani(liris)

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

"""
import sys

from setuptools import setup
import pkg_resources

VERSION = "1.0.0"

install_requires = []
tests_require = []

setup(
    name="websocket-client",
    version=VERSION,
    description="WebSocket client for Python with low level API options",
    long_description=open("README.md").read(),
    long_description_content_type='text/markdown',
    author="liris",
    author_email="liris.pp@gmail.com",
    license="LGPL version 2.1",
    url="https://github.com/websocket-client/websocket-client.git",
    download_url='https://github.com/websocket-client/websocket-client/releases',
    python_requires='>=3.6',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    project_urls={
        'Documentation': 'https://websocket-client.readthedocs.io/',
        'Source': 'https://github.com/websocket-client/websocket-client/',
    },
    keywords='websockets client',
    scripts=["bin/wsdump.py"],
    install_requires=install_requires,
    packages=["websocket", "websocket.tests"],
    package_data={
        'websocket.tests': ['data/*.txt']
    },
    tests_require=tests_require,
    test_suite="websocket.tests"
)
