# Autobahn Testsuite

General information and installation instructions are available at https://crossbar.io/autobahn/.

## Running the test suite

1. Install autobahn using `pip install autobahntestsuite`. Note that the the
[autobahn instructions](https://github.com/crossbario/autobahn-testsuite#installation)
state that this is an outdated installation method only for Python 2, so this
should be updated at some point.

2. To run the autobahn test suite against this library, use:
```
wstest -m fuzzingserver
python test_fuzzingclient.py
```
