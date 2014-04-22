from setuptools import setup

VERSION = "0.14.0"


setup(
    name="websocket-client",
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
    install_requires=[
        'backports.ssl_match_hostname',
        'six',
    ],
    packages=["tests", "websocket"],
    package_data={
        'tests': ['data/*.txt'],
        'websocket': ["cacert.pem"]
    },
)
