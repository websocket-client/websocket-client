# This is a small script to upload
# new releases to PyPI

# Create virtual environment
python3 -m venv /tmp/ws-venv/
source /tmp/ws-venv/bin/activate

# Install dependencies
pip3 install -U twine

# build the package
python -m build

# Run Twine check to verify descriptions are valid
twine check dist/*

# Upload to test PyPI first to verify everything
# The secure approach is to get an API token
# Then pass __token__ as the username and the token value as password
# https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives
twine upload --repository testpypi dist/*

# Now upload to production PyPI
# The secure approach is to get an API token
# Then pass __token__ as the username and the token value as password
# https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives
twine upload dist/*

# Clean up
# Delete the build/, dist/, and websocket_client.egg-info/ directories
rm -r build dist websocket_client.egg-info
