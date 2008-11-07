# Armon Dadgar
# 
# Creates python interface for windows api calls that are required 
#
# According to MSDN most of these calls are Windows 2K Pro and up
# Trying to replace the win32* stuff using ctypes

# Ctypes enable us to call the Windows API which written in C
from ctypes import * 

# Needed so that we can sleep
import time 

# Main Libraries
# kerneldll links to the library that has Windows Kernel Calls
kerneldll = windll.kernel32 
# memdll links to the library that has Windows Process/Thread Calls
memdll = windll.psapi

# Types
DWORD = c_ulong # Map Microsoft DWORD type to C long
HANDLE = c_ulong # Map Microsoft HANDLE type to C long
LONG = c_long # Map Microsoft LONG type to C long
SIZE_T = c_ulong # Map Microsoft SIZE_T type to C long

# Microsoft Constants
TH32CS_SNAPTHREAD = c_ulong(0x00000004) 
INVALID_HANDLE_VALUE = -1
THREAD_SUSPEND_RESUME = c_ulong(0x0002)
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_AND_TERMINATE = PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION
ERROR_ALREADY_EXISTS = 183
SYNCHRONIZE = 0x00100000L
WAIT_FAILED = 0xFFFFFFFF
WAIT_OBJECT_0 = 0x00000000L
WAIT_ABANDONED = 0x00000080L

# How many times to attempt sleeping/resuming thread or proces
# before giving up with failure
ATTEMPT_MAX = 10 

# Key Functions
# Maps Microsoft API calls to more convenient name for internal use
# Also abstracts the linking library for each function for more portability
_createSnapshot = kerneldll.CreateToolhelp32Snapshot # Makes snapshot of threads 
_openThread = kerneldll.OpenThread # Returns Thread Handle
_firstThread = kerneldll.Thread32First # Reads from Thread from snapshot
_nextThread = kerneldll.Thread32Next # Reads next Thread from snapshot
_suspendThread = kerneldll.SuspendThread # Puts a thread to sleep
_resumeThread = kerneldll.ResumeThread # Resumes Thread execution
_openProcess = kerneldll.OpenProcess # Returns Process Handle
_processTimes = kerneldll.GetProcessTimes # Returns data about Process CPU use
_processMemory = memdll.GetProcessMemoryInfo # Returns data on Process mem use
_processExitCode = kerneldll.GetExitCodeProcess # Gets Process Exit code
_terminateProcess = kerneldll.TerminateProcess # Kills a process
_closeHandle = kerneldll.CloseHandle # Closes any(?) handle object
_getLastError = kerneldll.GetLastError # Gets last error number of last error
_createMutex = kerneldll.CreateMutexW # Creates a Mutex, Unicode version
_openMutex = kerneldll.OpenMutexW # Opens an existing Mutex, Unicode Version
_releaseMutex = kerneldll.ReleaseMutex # Releases mutex
_waitForSingleObject = kerneldll.WaitForSingleObject # Waits to acquire mutex

# Classes
# Python Class which is converted to a C struct
# It encapsulates Thread Data, and is used in
# Windows Thread calls
class _THREADENTRY32(Structure): 
    _fields_ = [('dwSize', DWORD), 
                ('cntUsage', DWORD), 
                ('th32ThreadID', DWORD), 
                ('th32OwnerProcessID', DWORD),
                ('tpBasePri', LONG),
                ('tpDeltaPri', LONG),
                ('dwFlags', DWORD)]



# Python Class which is converted to a C struct
# It encapsulates Time data, with a low and high number
# We use it to get Process times (user/system/etc.)
class _FILETIME(Structure): 
    _fields_ = [('dwLowDateTime', DWORD), 
                ('dwHighDateTime', DWORD)]



# Python Class which is converted to a C struct
# It encapsulates data about a Processes 
# Memory usage. A pointer to the struct is passed
# to the Windows API
class _PROCESS_MEMORY_COUNTERS(Structure): 
    _fields_ = [('cb', DWORD), 
                ('PageFaultCount', DWORD), 
                ('PeakWorkingSetSize', SIZE_T), 
                ('WorkingSetSize', SIZE_T),
                ('QuotaPeakPagedPoolUsage', SIZE_T),
                ('QuotaPagedPoolUsage', SIZE_T),
                ('QuotaPeakNonPagedPoolUsage', SIZE_T),
                ('QuotaNonPagedPoolUsage', SIZE_T),
                ('PagefileUsage', SIZE_T),
                ('PeakPagefileUsage', SIZE_T)]


# Exceptions

# Gets thrown when a Tread Handle cannot be opened
class DeadThread(Exception): pass


# Gets thrown when a Process Handle cannot be opened
# Eventually a DeadThread will get escalated to DeadProcess
class DeadProcess(Exception): pass
       

# Gets thrown when a Mutex cannot be created
class FailedMutex(Exception): pass
 

# Gets thrown when a Mutex cannot be released because its not owned
class NonOwnedMutex(Exception): pass


# Global variables

# For each Mutex, record the lock count to properly release
_MutexLockCount = {}
   
# High level functions

# Returns list with the Thread ID of all threads associated with the PID
def getProcessThreads (PID):
  threads = [] # List object for threads
  currentThread = _THREADENTRY32() # Current Thread Pointer
  currentThread.dwSize = sizeof(_THREADENTRY32)
  
  # Create Handle to snapshot of all system threads
  handle = _createSnapshot(TH32CS_SNAPTHREAD, 0)
  
  # Check if handle was created successfully
  if handle == INVALID_HANDLE_VALUE:
      return []
  
  # Attempt to read snapshot
  if not _firstThread( handle, pointer(currentThread)):
    _closeHandle( handle )
    return []
  
  # Loop through threads, check for threads associated with the right process
  moreThreads = True
  while (moreThreads):
    # Check if current thread belongs to the process were looking for
    if currentThread.th32OwnerProcessID == PID: 
      threads.append(currentThread.th32ThreadID)
    moreThreads = _nextThread(handle, pointer(currentThread))
  
  # Cleanup snapshot
  _closeHandle(handle)
  
  return threads  


# Returns a handle for ThreadID  
def getThreadHandle (ThreadID):
  # Open handle to thread
  handle = _openThread(THREAD_SUSPEND_RESUME, 0, ThreadID)

  # Check for a successful handle
  if handle: 
    return handle
  else: # Raise exception on failure
    raise DeadThread, "Error opening thread handle! ThreadID: " + str(ThreadID) + " Error Str: " + str(WinError())  


# Suspend a thread with given ThreadID
def suspendThread (ThreadID):
  # Open handle to thread
  handle = getThreadHandle(ThreadID)

  # Try to suspend thread, save status of call
  status = _suspendThread(handle)

  # Close thread handle
  _closeHandle(handle)

  # -1 is returned on failure, anything else on success
  # Translate this to True and False
  return (not status == -1)


# Resume a thread with given ThreadID
def resumeThread (ThreadID):
  # Get thread Handle
  handle = getThreadHandle(ThreadID)

  # Attempt to resume thread, save status of call
  val = _resumeThread(handle)

  # Close Thread Handle
  _closeHandle(handle)

  # -1 is returned on failure, anything else on success
  # Translate this to True and False
  return (not val == -1)


# Suspend a process with given PID
def suspendProcess (PID):
  # Get List of threads related to Process
  threads = getProcessThreads(PID)

  # Suspend each thread serially
  for t in threads:
    sleep = False # Loop until thread sleeps
    attempt = 0 # Number of times we've attempted to suspend thread
    while not sleep:
      if (attempt > ATTEMPT_MAX):
        return False
      attempt = attempt + 1
      try:
        sleep = suspendThread(t)
      except DeadThread:
        # If the thread is dead, lets just say its asleep and continue
        sleep = True
  return True


# Resume a process with given PID
def resumeProcess (PID):
  # Get list of threads related to Process
  threads = getProcessThreads(PID)

  # Resume each thread
  for t in threads:
    wake = False # Loop until thread wakes up
    attempt = 0 # Number of attempts to resume thread
    while not wake: 
      if (attempt > ATTEMPT_MAX):
        return False
      attempt = attempt + 1
      try:
        wake = resumeThread(t)
      except DeadThread:
        # If the thread is dead, its hard to wake it up, so contiue
        wake = True
  return True


# Suspends a process and restarts after a given time interval
def timeoutProcess (PID, stime):
  try:
    # Attempt to suspend process, return immediately on failure
    if suspendProcess(PID):
      
      # Sleep for user defined period
      time.sleep (stime)

      # Attempt to resume process and return whether that succeeded
      return resumeProcess(PID)
    else:
      return False
  except DeadThread: # Escalate DeadThread to DeadProcess, because that is the underlying cause
    raise DeadProcess, "Failed to sleep or resume a thread!"
  

# Gets a process handle
def getProcessHandle (PID):
  # Get handle to process
  handle = _openProcess( PROCESS_QUERY_AND_TERMINATE, 0, PID)

  # Check if we successfully got a handle
  if handle:
    return handle
  else: # Raise exception on failure
    raise DeadProcess, "Error opening process handle! Process ID: " + str(PID) + " Error Str: " + str(WinError())
    

# Kill a process with specified PID
def killProcess (PID):
  try:
    # Get process handle
    handle = getProcessHandle(PID)
  except DeadProcess: # This is okay, since we're trying to kill it anyways
    return True

  dead = False # Status of Process we're trying to kill
  attempt = 0 # Attempt Number
 
  # Keep hackin' away at it
  while not dead:
    if (attempt > ATTEMPT_MAX):
      raise Exception, "Failed to kill process! Process ID: " + str(PID) + " Error Str: " + str(WinError())

    # Increment attempt count
    attempt = attempt + 1 

    # Attempt to terminate process
    # 0 is return code for failure, convert it to True/False
    dead = not 0 == _terminateProcess(handle, 0)

  # Close Process Handle
  _closeHandle(handle)

  return True


# Get information about a process CPU use times
def processTimes (PID):
  # Open process handle
  handle = getProcessHandle(PID)

  # Create all the structures needed to make API Call
  creationTime = _FILETIME()
  exitTime = _FILETIME()
  kernelTime = _FILETIME()
  userTime = _FILETIME()

  # Pass all the structures as pointers into processTimes
  _processTimes(handle, pointer(creationTime), pointer(exitTime), pointer(kernelTime), pointer(userTime))

  # Close Process Handle
  _closeHandle(handle)

  # Extract the values from the structures, and return then in a dictionary
  return {"CreationTime":creationTime.dwLowDateTime,"KernelTime":kernelTime.dwLowDateTime,"UserTime":userTime.dwLowDateTime}


# Get the exit code of a process
def processExitCode (PID):
  try:
    # Get process handle
    handle = getProcessHandle(PID)
  except DeadProcess:
    # Process is likely dead, so give anything other than 259
    return 0
 
  # Store the code, 0 by default
  code = c_int(0)

  # Pass in code as a pointer to store the output
  _processExitCode(handle, pointer(code))

  # Close the Process Handle
  _closeHandle(handle)
  return code.value


# Get information on process memory use
def processMemoryInfo (PID):
  # Open process Handle
  handle = getProcessHandle(PID)

  # Define structure to hold memory data
  meminfo = _PROCESS_MEMORY_COUNTERS()

  # Pass pointer to meminfo to processMemory to store the output
  _processMemory(handle, pointer(meminfo), sizeof(_PROCESS_MEMORY_COUNTERS))

  # Close Process Handle
  _closeHandle(handle)

  # Extract data from meminfo structure and return as python
  # dictionary structure
  return {'PageFaultCount':meminfo.PageFaultCount,
          'PeakWorkingSetSize':meminfo.PeakWorkingSetSize,
          'WorkingSetSize':meminfo.WorkingSetSize,
          'QuotaPeakPagedPoolUsage':meminfo.QuotaPeakPagedPoolUsage,
          'QuotaPagedPoolUsage':meminfo.QuotaPagedPoolUsage,
          'QuotaPeakNonPagedPoolUsage':meminfo.QuotaPeakNonPagedPoolUsage,
          'QuotaNonPagedPoolUsage':meminfo.QuotaNonPagedPoolUsage,
          'PagefileUsage':meminfo.PagefileUsage,
          'PeakPagefileUsage':meminfo.PeakPagefileUsage}  



# Creates and returns a handle to a Mutex
def createMutex(name):
  # Attempt to create Mutex
  handle = _createMutex(None, 0, name)

  # Check for a successful handle
  if not handle == False: 
    # Set the lock count to 1
    _MutexLockCount[handle] = 1
    return handle
  else: # Raise exception on failure
    raise FailedMutex, (_getLastError(), "Error creating mutex! Mutex name: " + str(name) + " Error Str: " + str(WinError()))


# Opens and returns a handle to a Mutex
def openMutex(name):
  # Attempt to create Mutex
  handle = _openMutex(SYNCHRONIZE, 0, name)

  # Check for a successful handle
  if not handle == False: 
    # Set the lock count to 1
    _MutexLockCount[handle] = 1
    return handle
  else: # Raise exception on failure
    raise FailedMutex, (_getLastError(), "Error opening mutex! Mutex name: " + str(name) + " Error Str: " + str(WinError()))


# Waits for specified interval to acquire Mutex
# time should be in milliseconds
def acquireMutex(handle, time):
  # Wait up to time to acquire lock, fail otherwise
  val = _waitForSingleObject(handle, time)

  # Update lock count
  _MutexLockCount[handle] += 1

  # WAIT_OBJECT_0 is returned on success, other on failure
  return (val == WAIT_OBJECT_0) or (val == WAIT_ABANDONED)


# Releases a mutex
def releaseMutex(handle):
  # Get the lock count
  count = _MutexLockCount[handle]

  # 0 out the count
  _MutexLockCount[handle] = 0

  # Attempt to release a Mutex
  for i in range(0, count):
    try:
      release = _releaseMutex(handle)

      # 0 return value means failure
      if release == 0:
        raise NonOwnedMutex, (_getLastError(), "Error releasing mutex! Mutex id: " + str(handle) + " Error Str: " + str(WinError()))
    except NonOwnedMutex, e:
      if (e[0] == 288): # 288 is for non-owned mutex, which is ok
        pass
      else:
        raise
    