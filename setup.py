from setuptools import setup
import sys

VERSION = "0.15.0"

install_requires = ["six"]
if sys.version_info[0] == 2:
    name="websocket-client"
    install_requires.append('backports.ssl_match_hostname')
    if sys.version_info[1] < 7:
        install_requires.append('unittest2')
        install_requires.append('argparse')
else:
    # for backword compatible.
    name="websocket-client-py3"

setup(
    name=name,
    version=VERSION,
    description="WebSocket client for python. hybi13 is supported.",
    long_description=open("README.rst").read(),
    author="liris",
    author_email="liris.pp@gmail.com",
    license="LGPL",
    url="https://github.com/liris/websocket-client",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    keywords='websockets',
    scripts=["bin/wsdump.py"],
    install_requires=install_requires,
    packages=["tests", "websocket"],
    package_data={
        'tests': ['data/*.txt'],
        'websocket': ["cacert.pem"]
    },
)
