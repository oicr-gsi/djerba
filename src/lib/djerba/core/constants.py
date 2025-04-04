CORE = 'core'
NULL = '__DJERBA_NULL__'
VERSION = 'version'
TEXT_ENCODING = 'utf-8'

# shared constants for core classes
ATTRIBUTES = 'attributes'
DEPENDS_CONFIGURE = 'depends_configure'
DEPENDS_EXTRACT = 'depends_extract'
# render dependencies are intentionally not defined
CLINICAL = 'clinical'
RESEARCH = 'research'
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
AUTHOR = 'author'
EXTRACT_TIME = 'extract_time'
INPUT_PARAMS_FILE = 'input_params'
REQUISITION_ID = 'requisition_id'
STYLESHEET = 'stylesheet'
DOCUMENT_CONFIG = 'document_config'
PLUGINS = 'plugins'
MERGERS = 'mergers'
CONFIG = 'config'
HTML_CACHE = 'html_cache'
COMPONENT_START = 'DJERBA_COMPONENT_START'
COMPONENT_END = 'DJERBA_COMPONENT_END'
CORE_VERSION = 'core_version'

# keys for sample ID file written by provenance helper
# TODO remove duplicate versions from provenance helper main
STUDY_TITLE = 'study_title'
ROOT_SAMPLE_NAME = 'root_sample_name'
PATIENT_STUDY_ID = 'patient_study_id'
TUMOUR_ID = 'tumour_id'
NORMAL_ID = 'normal_id'

# core config defaults
DEFAULT_PATH_INFO = "path_info.json"
DEFAULT_INPUT_PARAMS = "input_params.json"
DEFAULT_SAMPLE_INFO = "sample_info.json"
DEFAULT_CSS = "stylesheet.css"
DEFAULT_AUTHOR = "CGI Author"
DEFAULT_DOCUMENT_CONFIG = "document_config.json"

# archive config
ARCHIVE_HEADER = 'archive'
USERNAME = 'username'
PASSWORD = 'password'
ADDRESS = 'address'
PORT = 'port'
DATABASE_NAME = 'database_name'
# environment variable for database config
ARCHIVE_CONFIG_VAR = 'DJERBA_ARCHIVE_CONFIG'


# keywords for document rendering
BODY = 'body'
DOCUMENTS = 'documents'
DOCUMENT_HEADER = 'document_header'
DOCUMENT_FOOTER = 'document_footer'
DOCUMENT_TYPES = 'document_types'
DOCUMENT_SETTINGS = 'document_settings'
FOOTER = 'footer'
MERGE_LIST = 'merge_list'
MERGED_FILENAME = 'merged_filename'
PAGE_FOOTER = 'page_footer'
PDF_FOOTERS = 'pdf_footers'

# keywords for plugin structure
RESULTS = 'results'
MERGE_INPUTS = 'merge_inputs'
SUMMARY = 'Summary'

# keyword for OncoKB level
ONCOKB = 'OncoKB'

# JSON file suffix
REPORT_JSON_SUFFIX = '_report.json'

# root directory pattern for WHIZBAM files
WHIZBAM_PATTERN_ROOT='/.mounts/labs/prod/whizbam'

# component versions/URLs
COMPONENT_FILENAME = 'component_info.json'
UNDEFINED_VERSION = 'version_not_defined'
UNDEFINED_URL = 'url_not_defined'
VERSION_KEY = 'version'
URL_KEY = 'url'
DJERBA_CORE_URL = 'https://github.com/oicr-gsi/djerba'
