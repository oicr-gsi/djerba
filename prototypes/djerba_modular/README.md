# Djerba modular demo

Simple demonstration of a plugin structure for Djerba:
- Import two different plugins
- Do configuration and extraction
- Write JSON and HTML with the combined plugin outputs

Note that we use Python's [importlib](https://docs.python.org/3/library/importlib.html) to import modules, given their names in string format from an INI file.

## Usage

- `export PYTHONPATH=${DJERBA_SOURCE_DIR}/prototypes:$PYTHONPATH`
- `cd ${DJERBA_SOURCE_DIR}/prototypes/djerba_modular`
- `./core/plugin_runner.py demo/config.ini $OUT_DIR`
