# Storing the version here so:
# 1) we don't load dependencies by storing it in __init__.py
# 2) we can import it in setup.py for the same reason
# 3) it only needs to be stored in one place
# See https://stackoverflow.com/a/16084844
__version__ = '0.3.10'
