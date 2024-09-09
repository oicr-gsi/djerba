# pyinstaller hook script, used at build time for mini-Djerba
import os
pkg_dir = os.path.dirname(os.path.realpath(__file__))
os.environ["PATH"] = pkg_dir+":"+os.environ["PATH"]
os.environ["DJERBA_BASE_DIR"] = os.path.join(pkg_dir, 'djerba')
os.environ["DJERBA_RUN_DIR"] = os.path.join(pkg_dir, 'djerba', 'data')
