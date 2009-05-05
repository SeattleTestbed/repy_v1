"""
Author: Armon Dadgar
Start Date: April 7th, 2009

Description:
  This file provides a python interface to low-level system call on the darwin (OSX) platform.
  It is designed to abstract away the C-level detail and provide a high-level method of doing
  common management tasks.

"""

import ctypes       # Allows us to make C calls
import ctypes.util  # Helps to find the C library

import os           # Provides some convenience functions
import time         # Used for time.time()
import subprocess   # Used for the thread count

import nix_common_api as nixAPI # Import the Common API

# Manually import the common functions we want
existsOutgoingNetworkSocket = nixAPI.existsOutgoingNetworkSocket
existsListeningNetworkSocket = nixAPI.existsListeningNetworkSocket
getAvailableInterfaces = nixAPI.getAvailableInterfaces
getInterfaceIPAddresses = nixAPI.getInterfaceIPAddresses

# Get the standard library
libc = ctypes.CDLL(ctypes.util.find_library("c"))

# Global Variables

# Storing this information allows us to make a single call to update the structure,
# but provide information about multiple things. E.g.memory and CPU
# Without this, each piece of info would require a call
# Also allows us to only allocate memory once, rather than every call
lastProcInfoStruct = None   # The last structure

# Functions
_calloc = libc.calloc
_proc_pidinfo = libc.proc_pidinfo
_free = libc.free

# Constants
PROC_PIDTASKINFO = 4
CTL_KERN = 1
KERN_BOOTTIME = 21
TwoIntegers = ctypes.c_int * 2 # C array with 2 ints

# Structures

# Provides the struct proc_taskinfo structure, which is used
# to retrieve information about a process by PID
class proc_taskinfo(ctypes.Structure):
  _fields_ = [("pti_virtual_size", ctypes.c_uint64),
              ("pti_resident_size", ctypes.c_uint64),
              ("pti_total_user", ctypes.c_uint64),
              ("pti_total_system", ctypes.c_uint64),
              ("pti_threads_user", ctypes.c_uint64),
              ("pti_threads_system", ctypes.c_uint64),
              ("pti_policy", ctypes.c_int32),
              ("pti_faults", ctypes.c_int32),
              ("pti_pageins", ctypes.c_int32),
              ("pti_cow_faults", ctypes.c_int32),
              ("pti_messages_sent", ctypes.c_int32),
              ("pti_messages_received", ctypes.c_int32),
              ("pti_syscalls_mach", ctypes.c_int32),
              ("pti_syscalls_unix", ctypes.c_int32),
              ("pti_csw", ctypes.c_int32),
              ("pti_threadnum", ctypes.c_int32),
              ("pti_numrunning", ctypes.c_int32),
              ("pti_priority", ctypes.c_int32)]

class timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long),
                ("tv_usec", ctypes.c_long)]
              
# Store the size of this structure
PROC_TASKINFO_SIZE = ctypes.sizeof(proc_taskinfo)

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

def _castCallocType(casttype):
  """
  <Purpose>
    Casts the return type of calloc. This is like doing (type*)calloc(...) in C
  
  <Arguments>
    type: The type to cast as.
  """
  _calloc.restype = casttype


def _getProcInfoByPID(PID):
  """
  <Purpose>
    Immediately updates the internal proc_taskinfo structure.
  
  <Arguments>
    PID: The Process Identifier for which data should be retrieved
  
  <Exceptions>
    Raises an Exception if there is an error.
  
  <Returns>
    Nothing
  """
  global lastProcInfoStruct
  
  # Check if we need to allocate a structure
  if lastProcInfoStruct == None:
    # Cast calloc as a pointer to the proc_taskinfo structure
    _castCallocType(ctypes.POINTER(proc_taskinfo))
    
    # Allocate a structure
    lastProcInfoStruct = _calloc(1, PROC_TASKINFO_SIZE)
  
  # Make the call to update
  status = _proc_pidinfo(PID, PROC_PIDTASKINFO, ctypes.c_uint64(0),  lastProcInfoStruct, PROC_TASKINFO_SIZE)
  
  if status == 0:
    # This means to data was written, this is an error
    raise Exception,"Errno:"+str(getCtypesErrno())+", Error: "+getCtypesErrorStr()


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
  
  # Get the process info by dereferencing the pointer
  procInfo = lastProcInfoStruct.contents
  
  # Get the total time from the user time and system time
  # Divide 1 billion since time is in nanoseconds
  totalTime = procInfo.pti_total_user/1000000000.0 + procInfo.pti_total_system/1000000000.0
  
  # Return the total time
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
  
  # Get the process info by dereferencing the pointer
  procInfo = lastProcInfoStruct.contents
  
  # Fetch the RSS
  RSS = procInfo.pti_resident_size
  
  # Return the info
  return RSS


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
  # Use PS since it is setuid and can get the info for us
  # Pipe into wc because I'm too lazy to do it manually
  cmd = "ps axM | wc -l"
  
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

def cleanUp():
  """
  <Purpose>
    Allows the module to cleanup any internal state and release memory allocated.
  """
  global lastProcInfoStruct
  
  # Check if lastProcInfoStruct is allocated and free it if necessary
  if lastProcInfoStruct != None:
    _free(lastProcInfoStruct)
  



