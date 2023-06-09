import sys
import pkg_resources
from setuptools import setup, find_packages

"""
setup.py
websocket - WebSocket client library for Python

Copyright 2022 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

VERSION = "1.5.3"

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
    license="Apache-2.0",
    url="https://github.com/websocket-client/websocket-client.git",
    download_url='https://github.com/websocket-client/websocket-client/releases',
    python_requires='>=3.7',
    extras_require={
        "test": ["websockets"],
        "optional": ["python-socks", "wsaccel"],
        "docs": ["Sphinx >= 3.4", "sphinx_rtd_theme >= 0.5"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
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
    entry_points={
        'console_scripts': [
            'wsdump=websocket._wsdump:main',
        ],
    },
    install_requires=install_requires,
    packages=find_packages(),
    package_data={
        'websocket.tests': ['data/*.txt']
    },
    tests_require=tests_require,
    test_suite="websocket.tests"
)
