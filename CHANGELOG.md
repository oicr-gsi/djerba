# CHANGELOG

## Unreleased
- `djerba.py` script to run Djerba functions from the command line
- `djerba` Python package with modules to:
  - Validate Djerba config: `validate.py`
  - Compute genetic alteration metrics: `genetic_alteration.py`
  - Contain sample attributes: `sample.py`
  - Write ShinyReport config: `report.py`
  - Write cBioPortal files: `study.py`, `components.py`
- Tests for new modules, including:
  - Dry-run test of cBioPortal study/sample metadata
  - Live test of cBioPortal mutation data, with MAF input
  - Test for dummy version of ShinyReport JSON output
- `setup.py` script for installation
