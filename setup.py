from pathlib import Path
from setuptools import find_packages, setup

"""
setup.py
websocket - WebSocket client library for Python

Copyright 2026 engn33r

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

VERSION = "1.9.2"

install_requires: list[str] = []
setup(
    name="websocket-client",
    version=VERSION,
    description="WebSocket client for Python with low level API options",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="liris",
    author_email="liris.pp@gmail.com",
    maintainer="engn33r",
    maintainer_email="websocket.client@proton.me",
    license="Apache-2.0",
    url="https://github.com/websocket-client/websocket-client",
    download_url="https://github.com/websocket-client/websocket-client/releases",
    python_requires=">=3.10",
    extras_require={
        "test": ["pytest", "websockets"],
        "optional": ["python-socks", "wsaccel"],
        "docs": ["Sphinx >= 6.0", "sphinx_rtd_theme >= 1.1.0", "myst-parser >= 2.0.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    project_urls={
        "Documentation": "https://websocket-client.readthedocs.io/",
        "Source": "https://github.com/websocket-client/websocket-client/",
    },
    keywords="websockets client",
    entry_points={
        "console_scripts": [
            "wsdump=websocket._wsdump:main",
        ],
    },
    install_requires=install_requires,
    packages=find_packages(),
    package_data={"websocket.tests": ["data/*.txt"]},
)
