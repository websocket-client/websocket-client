# Autobahn Testsuite

General information and installation instructions are available at https://crossbar.io/autobahn/.

## Running the test suite

1. Install autobahn using `pip2 install autobahntestsuite`. Note that the
[autobahn instructions](https://github.com/crossbario/autobahn-testsuite#installation)
states that this is an outdated installation method only for Python 2, so this
should be updated at some point.

2. (Optional) If you try step 1 and get an error from gcc stating
"Python.h: No such file or directory", then install the python-dev package
(specifically the one for Python 2)

3. Run `wstest -m fuzzingserver`

4. Make note of the port number that the server from step 3 is running on, then
modify the `test_fuzzingclient.py` file accordingly

5. Run `python test_fuzzingclient.py`

6. When the test is complete, the results will be saved in a directory named
`reports`
