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

VERSION = "0.58.0"
NAME = "websocket_client"

install_requires = ["six"]
tests_require = []

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
        tests_require.append('unittest2==0.8.0')

insecure_pythons = '2.6, ' + ', '.join("2.7.{pv}".format(pv=pv) for pv in range(10))

extras_require = {
    ':python_version in "{ips}"'.format(ips=insecure_pythons):
        ['backports.ssl_match_hostname'],
    ':python_version in "2.6"': ['argparse'],
}

try:
    if 'bdist_wheel' not in sys.argv:
        for key, value in extras_require.items():
            if key.startswith(':') and pkg_resources.evaluate_marker(key[1:]):
                install_requires.extend(value)
except Exception:
    import logging
    logging.getLogger(__name__).exception(
        'Something went wrong calculating platform specific dependencies, so '
        "you're getting them all!"
    )
    for key, value in extras_require.items():
        if key.startswith(':'):
            install_requires.extend(value)

setup(
    name=NAME,
    version=VERSION,
    description="WebSocket client for Python with low level API options",
    long_description=open("README.md").read(),
    long_description_content_type='text/markdown',
    author="liris",
    author_email="liris.pp@gmail.com",
    license="LGPL version 2.1",
    url="https://github.com/websocket-client/websocket-client.git",
    download_url='https://github.com/websocket-client/websocket-client/releases',
    python_requires='>=2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
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
