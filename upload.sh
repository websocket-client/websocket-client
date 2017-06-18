python -m venv /tmp/ws-venv/
source /tmp/ws-venv/bin/activate
pip install -U pip setuptools wheel
python setup.py sdist bdist_wheel upload
