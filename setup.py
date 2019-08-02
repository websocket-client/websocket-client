import sys

from setuptools import setup
import pkg_resources

VERSION = "0.56.0"
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
    description="WebSocket client for Python. hybi13 is supported.",
    long_description=open("README.rst").read(),
    author="liris",
    author_email="liris.pp@gmail.com",
    license="BSD",
    url="https://github.com/websocket-client/websocket-client.git",
    python_requires='>=2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
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
    packages=["websocket", "websocket.tests"],
    package_data={
        'websocket.tests': ['data/*.txt']
    },
    tests_require=tests_require,
    test_suite="websocket.tests"
)
