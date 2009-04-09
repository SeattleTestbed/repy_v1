"""
Author: Armon Dadgar
Start Date: April 7th, 2009

Description:
  This file provides a python interface to low-level system call on the Linux platform.
  It is designed to abstract away the C-level detail and provide a high-level method of doing
  common management tasks.

"""

import ctypes       # Allows us to make C calls
import ctypes.util  # Helps to find the C library

import os           # Provides some convenience functions
import time         # Provides time.time
import subprocess

import freebsd_kinfo  # Imports the kinfo structure, along with others

# Get the standard library
libc = ctypes.CDLL(ctypes.util.find_library("c"))

# Globals
# Cache the last process info struct so as to avoid redundant memory allocation
# and to fetch additional info without constantly updating
lastProcInfoStruct = None
lastProcInfoSize   = 0    # Stores the size of the struct

# Functions
_sysctl = libc.sysctl # Makes system calls

# Constants
CTL_KERN = 1
KERN_PROC = 14
KERN_PROC_PID = 1
FourIntegers = ctypes.c_int * 4 # A C array with 4 ints, used for syscalls
PAGE_SIZE = libc.getpagesize() # Call into libc to get our page size
KERN_BOOTTIME = 21
TwoIntegers = ctypes.c_int * 2 # C array with 2 ints

# Structures
kinfo_proc = freebsd_kinfo.kinfo_proc # Import from the external file

class timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long),
                ("tv_usec", ctypes.c_long)]

# This functions helps to conveniently retrieve the errno
# of the last call. This is a bit tedious to do, since 
# Python doesn't understand that this is a globally defined int
def getCtypesErrno():
  errnoPointer = ctypes.cast(libc.errno, ctypes.POINTER(ctypes.c_int32))
  errVal = errnoPointer.contents
  return errVal.value

# Returns the string version of the errno  
def getCtypesErrorStr():
  errornum = getCtypesErrno()
  return ctypes.cast(libc.strerror(errornum), ctypes.c_char_p).value
  

def _getProcInfoByPID(PID):
  """
  <Purpose>
    Immediately updates the internal kinfo_proc structure.
  
  <Arguments>
    PID: The Process Identifier for which data should be retrieved
  
  <Exceptions>
    Raises an Exception if there is an error.
  
  <Returns>
    Nothing
  """
  global lastProcInfoStruct
  global lastProcInfoSize
  
  # Create the argument array
  mib = FourIntegers(CTL_KERN, KERN_PROC, KERN_PROC_PID, PID)
  
  # Check if we need to allocate a structure
  if lastProcInfoStruct == None:
    # Allocate a kinfo structure
    lastProcInfoStruct = kinfo_proc(0)
    lastProcInfoSize  = ctypes.c_int(0)
    
    # Make a system call without a pointer to the kinfo structure, this sets
    # ths proper size of the structure for future system calls
    status = _sysctl(mib, 4, None, ctypes.byref(lastProcInfoSize), None, 0)
    
    # Check the status
    if status != 0:
      raise Exception,"Fatal error with sysctl. Errno:"+str(getCtypesErrno())+", Error: "+getCtypesErrorStr()
  
  
  # Make the call to update
  status = _sysctl(mib, 4, ctypes.byref(lastProcInfoStruct), ctypes.byref(lastProcInfoSize), None, 0)
  
  # Check the status
  if status != 0:
    raise Exception,"Fatal error with sysctl. Errno:"+str(getCtypesErrno())+", Error: "+getCtypesErrorStr()
    

def getProcessCPUTime(PID):
  """
  <Purpose>
    Returns the total CPU time used by a process.

  <Arguments>
    PID: The process identifier for the process to query.

  <Exceptions>
    See _getProcInfoByPID.

  <Returns>
    The total cpu time.
  """
  global lastProcInfoStruct
  
  # Update the info
  _getProcInfoByPID(PID)
  
  # Get the rusage field in the structure
  ru = lastProcInfoStruct.ki_rusage
  
  # Calculate user time and system, for the process and its children,
  # divide by 1 million since the usec field is in microseconds
  utime = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec/1000000.0
  stime = ru.ru_stime.tv_sec + ru.ru_stime.tv_usec/1000000.0

  # Switch ru to the child structure
  ru = lastProcInfoStruct.ki_rusage_ch

  utime_ch = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec/1000000.0
  stime_ch = ru.ru_stime.tv_sec + ru.ru_stime.tv_usec/1000000.0
  
  # Calculate the total time
  totalTime = utime + stime + utime_ch + stime_ch
  
  return totalTime



def getProcessRSS(forceUpdate=False,PID=None):
  """
  <Purpose>
    Returns the Resident Set Size of a process. By default, this will
    return the information cached by the last call to _getProcInfoByPID.
    This call is used in getProcessCPUTime.

  <Arguments>
    forceUpdate:
      Allows the caller to force a data update, instead of using the cached data.

    PID:
      If forceUpdate is True, this parameter must be specified to force the update.

  <Exceptions>
    See _getProcInfoByPID.

  <Returns>
    The RSS of the process in bytes.
  """
  global lastProcInfoStruct
  
  # Check if an update is being forced
  if forceUpdate and PID != None:
    # Update the info
    _getProcInfoByPID(PID)
  
  # Get RSS
  rss_pages = lastProcInfoStruct.ki_rssize
  rss_bytes = rss_pages * PAGE_SIZE
  
  return rss_bytes


# Return the timeval struct with our boottime
def _getBoottimeStruct():
  # Get an array with 2 elements, set the syscall parameters
  mib = TwoIntegers(CTL_KERN, KERN_BOOTTIME)

  # Get timeval structure, set the size
  boottime = timeval()                
  size = ctypes.c_size_t(ctypes.sizeof(boottime))

  # Make the syscall
  libc.sysctl(mib, 2, ctypes.pointer(boottime), ctypes.pointer(size), None, 0)
  
  return boottime

def getSystemUptime():
  """
  <Purpose>
    Returns the system uptime.

  <Returns>
    The system uptime.  
  """
  # Get the boot time struct
  boottime = _getBoottimeStruct()

  # Calculate uptime from current time
  uptime = time.time() - boottime.tv_sec+boottime.tv_usec*1.0e-6

  return uptime

def getUptimeGranularity():
  """
  <Purpose>
    Determines the granularity of the getSystemUptime call.

  <Returns>
    A numerical representation of the minimum granularity.
    E.g. 2 digits of granularity would return 0.01
  """
  # Get the boot time struct
  boottime = _getBoottimeStruct()
  
  # Check if the number of nano seconds is 0
  if boottime.tv_usec == 0:
    granularity = 0
  
  else:
    # Convert nanoseconds to string
    nanoSecStr = str(boottime.tv_usec)
    
    # Justify with 0's to 9 digits
    nanoSecStr = nanoSecStr.rjust(9,"0")
    
    # Strip the 0's on the other side
    nanoSecStr = nanoSecStr.rstrip("0")
    
    # Get granularity from the length of the string
    granularity = len(nanoSecStr)

  # Convert granularity to a number
  return pow(10, 0-granularity)



def getSystemThreadCount():
  """
  <Purpose>
    Returns the number of active threads running on the system.

  <Returns>
    The thread count.
  """
  # Use PS since it is can get the info for us
  # Pipe into wc because I'm too lazy to do it manually
  cmd = "ps axH | wc -l"

  process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, close_fds=True)

  # Get the output
  threads = process.stdout.read()

  # Close the pipe
  process.stdout.close()

  # Strip the whitespace
  threads = threads.strip()

  # Convert to int
  threads = int(threads)

  return threads


