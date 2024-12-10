from enum import Enum

class ChannelType(Enum):
    COMBO = 'combo'
    ARCHIVE = 'archive'

class FileExtensions(Enum):
    ZIP = '.zip'
    RAR = '.rar'
    SEVEN_Z = '.7z'

# Regex patterns for file processing
REGEX_PATTERNS = {
    'pattern1': r'URL:\s(.*?)[|\r]\nUsername:\s(.*?)[|\r]\nPassword:\s(.*?)[|\r]\n',
    'pattern2': r'URL:\s(.*)\nUSER:\s(.*)\nPASS:\s(.*)',
    'pattern3': r'url:\s*(.*?)\r?\nlogin:\s*(.*?)\r?\npassword:\s*(.*?)(\r?\n|$)'
}

# Minimum file size for archive processing (179MB)
MIN_ARCHIVE_SIZE = 179 * 1024 * 1024

# Special file handling
SPECIAL_PASSWORDS = {
    "example": "t.me/example"
}

# Protocol prefixes
PROTOCOLS = ['http', 'https', 'smtp', 'android', 'imap', 'oauth']


# Special URLs and logins (can be parts of the field, for ex. for accounts.google.com it can be accounts.google) that you'll get notified about if found in the output before ingestion
SPECIAL_URLS = ['example.']

SPECIAL_LOGINS = ['@gmail.com', 'admin']

# File processing
EXCLUDED_LINES = ['']