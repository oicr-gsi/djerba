CORE = 'core'
NULL = '__NULL__'

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

# keys for core config/extract
REPORT_ID = 'report_id'
REPORT_VERSION = 'report_version'
ARCHIVE_NAME = 'archive_name'
ARCHIVE_URL = 'archive_url'
AUTHOR = 'author'
LOGO = 'logo'
PREAMBLE = 'preamble'
SAMPLE_INFO = 'sample_info'
STYLESHEET = 'stylesheet'
DOCUMENT_HEADER = 'document_header'
RUO_HEADER = 'ruo_header'
DOCUMENT_FOOTER = 'document_footer'

PLUGINS = 'plugins'
MERGERS = 'mergers'
CONFIG = 'config'

# keys for sample ID file written by provenance helper
TUMOUR_ID = 'tumour_id'
NORMAL_ID = 'normal_id'

# core config defaults
DEFAULT_SAMPLE_INFO = "sample_info.json"
DEFAULT_PREAMBLE = "preamble.html"
DEFAULT_CSS = "stylesheet.css"
DEFAULT_AUTHOR = "CGI Author"
DEFAULT_LOGO = "OICR_Logo_RGB_ENGLISH.png"
DEFAULT_DH = "document_header.html"
DEFAULT_DF = "document_footer.html"
DEFAULT_RUO_HEADER = "ruo_header.html"
