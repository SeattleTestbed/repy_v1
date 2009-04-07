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

# Structures
kinfo_proc = freebsd_kinfo.kinfo_proc # Import from the external file

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



