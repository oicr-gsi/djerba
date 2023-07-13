CORE = 'core'

# environment variables
DJERBA_DATA_DIR_VAR = 'DJERBA_DATA_DIR'
DJERBA_PRIVATE_DIR_VAR = 'DJERBA_PRIVATE_DIR'
DJERBA_TEST_DIR_VAR = 'DJERBA_TEST_DIR'

# shared constants for core classes
ATTRIBUTES = 'attributes'
DEPENDS_CONFIGURE = 'depends_configure'
DEPENDS_EXTRACT = 'depends_extract'
# render dependencies are intentionally not defined
CLINICAL = 'clinical'
SUPPLEMENTARY = 'supplementary'
CONFIGURE_PRIORITY = 'configure_priority'
EXTRACT_PRIORITY = 'extract_priority'
RENDER_PRIORITY = 'render_priority'
PRIORITY_KEYS = [
    CONFIGURE_PRIORITY,
    EXTRACT_PRIORITY,
    RENDER_PRIORITY
]
RESERVED_PARAMS = [
    ATTRIBUTES,
    DEPENDS_CONFIGURE,
    DEPENDS_EXTRACT,
    CONFIGURE_PRIORITY,
    EXTRACT_PRIORITY,
    RENDER_PRIORITY
]
PRIORITIES = 'priorities'
CONFIGURE = 'configure'
EXTRACT = 'extract'
RENDER = 'render'

# attribute names
CLINICAL = 'clinical'
SUPPLEMENTARY = 'supplementary'

# core config elements
DONOR = 'donor'
PROJECT = 'project'

# keywords for component args
IDENTIFIER = 'identifier'
MODULE_DIR = 'module_dir'
LOG_LEVEL = 'log_level'
LOG_PATH = 'log_path'
WORKSPACE = 'workspace'

# keys for the extraction framework
REPORT_ID = 'report_id'
ARCHIVE_NAME = 'archive_name'
ARCHIVE_URL = 'archive_url'
AUTHOR = 'author'
LOGO = 'logo'
PREAMBLE = 'preamble'
STYLESHEET = 'stylesheet'
PLUGINS = 'plugins'
MERGERS = 'mergers'
CONFIG = 'config'
