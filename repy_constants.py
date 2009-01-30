# File Holds Constant values for Repy
#
#

# Holds the path to a python installation
PATH_PYTHON_INSTALL = "\\Storage Card\\Program Files\\Python25\\python.exe"

# Default Python Flags
# e.g. The "/new" flag is necessary for PythonCE to allow multiple instances
# The /nopcceshell disables the PythonCE window from opening and annoying the user
PYTHON_DEFAULT_FLAGS = "/new /nopcceshell "
#PYTHON_DEFAULT_FLAGS = ""

# Repy Installation path
PATH_SEATTLE_INSTALL = "\\Storage Card\\Program Files\\Python25\\Lib\\SEATTLE\\"
#PATH_SEATTLE_INSTALL = "Z:\\Projects\\seattle\\trunk\\repy\\"

# Current Working directory
REPY_CURRENT_DIR = "."

# Polling Frequency for different Platforms, This is for non-CPU resources
# Poll non-cpu resources less often to reduce overhead
# Memory may need to be tighted, since it is possible to debilitate a system in less time than this.
RESOURCE_POLLING_FREQ_LINUX = .5 # Linux
RESOURCE_POLLING_FREQ_WIN = .5 # Windows
RESOURCE_POLLING_FREQ_WINCE = 2 # Mobile devices are pretty slow

# CPU Polling Frequency for different Platforms
CPU_POLLING_FREQ_LINUX = .1 # Linux
CPU_POLLING_FREQ_WIN = .1 # Windows
CPU_POLLING_FREQ_WINCE = .5 # Mobile devices are pretty slow
