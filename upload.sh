# This is a small script to upload
# new releases to PyPI

# Create virtual environment
python3 -m venv /tmp/ws-venv/
source /tmp/ws-venv/bin/activate

# Install dependencies
pip3 install -U setuptools wheel twine

# build the package
python3 setup.py sdist bdist_wheel

# Run Twine check to verify descriptions are valid
twine check dist/*

# Upload to test PyPI first to verify everything
twine upload --repository testpypi dist/*

# Now upload to actual PyPI
twine upload dist/*
