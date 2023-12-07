CORE = 'core'
NULL = '__DJERBA_NULL__'
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
ARCHIVE_NAME = 'archive_name'
ARCHIVE_URL = 'archive_url'
AUTHOR = 'author'
EXTRACT_TIME = 'extract_time'
SAMPLE_INFO = 'sample_info'
STYLESHEET = 'stylesheet'
DOCUMENT_CONFIG = 'document_config'
PLUGINS = 'plugins'
MERGERS = 'mergers'
CONFIG = 'config'
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
DEFAULT_SAMPLE_INFO = "sample_info.json"
DEFAULT_CSS = "stylesheet.css"
DEFAULT_AUTHOR = "CGI Author"
DEFAULT_DOCUMENT_CONFIG = "document_config.json"

# archive config
ARCHIVE_CONFIG = 'archive_config.ini'
ARCHIVE_HEADER = 'archive'
USERNAME = 'username'
PASSWORD = 'password'
ADDRESS = 'address'
PORT = 'port'

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

# keywords for plugin structure
RESULTS = 'results'
MERGE_INPUTS = 'merge_inputs'
SUMMARY = 'Summary'

# keyword for OncoKB level
ONCOKB = 'OncoKB'
