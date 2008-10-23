# Armon Dadgar
#
# Trying to replace the win32* stuff to be compatible on Mobile/CE platforms using ctypes

from ctypes import * 
import os

# Define important values
maindll = cdll.coredll # Library to link against
GetThreadTimes = maildll.GetThreadTimes

