# File Holds Constant values for Repy
#
#

# Holds the path to a python installation
PATH_PYTHON_INSTALL = "\\Storage Card\\Program Files\\Python25\\python.exe"

# Default Python Flags
# e.g. The "/new" flag is necessary for PythonCE to allow multiple instances
PYTHON_DEFAULT_FLAGS = "/new /nopcceshell "

# Repy Installation path
#PATH_SEATTLE_INSTALL = "\\Storage Card\\Program Files\\Python25\\Lib\\SEATTLE\\"
PATH_SEATTLE_INSTALL = "Z:\\trunk\\repy\\"

# Current Working directory
REPY_CURRENT_DIR = "."

# Polling Frequency for different Platforms
RESOURCE_POLLING_FREQ_LINUX = .1 # Linux can check relatively quickly
RESOURCE_POLLING_FREQ_WIN = .2 # Windows crashes at .1
RESOURCE_POLLING_FREQ_WINCE = 1 # Mobile devices are pretty slow

