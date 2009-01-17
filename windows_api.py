# Armon Dadgar
# 
# Creates python interface for windows api calls that are required 
#
# According to MSDN most of these calls are Windows 2K Pro and up
# Trying to replace the win32* stuff using ctypes

# Ctypes enable us to call the Windows API which written in C
import ctypes

# Needed so that we can sleep
import time 

# Used for OS detection
import os

# Detect whether or not it is Windows CE/Mobile
MobileCE = False
if os.name == 'ce':
  MobileCE = True

# Main Libraries
# Loaded depending on OS
if MobileCE:
  # kerneldll links to the library that has Windows Kernel Calls
  kerneldll = ctypes.cdll.coredll

  # Toolhelp library
  # Contains Tool helper functions
  toolhelp = ctypes.cdll.toolhelp

else:
  # kerneldll links to the library that has Windows Kernel Calls
  kerneldll = ctypes.windll.kernel32 
  # memdll links to the library that has Windows Process/Thread Calls
  memdll = ctypes.windll.psapi

# Types
DWORD = ctypes.c_ulong # Map Microsoft DWORD type to C long
WORD = ctypes.c_ushort # Map microsoft WORD type to C ushort
HANDLE = ctypes.c_ulong # Map Microsoft HANDLE type to C long
LONG = ctypes.c_long # Map Microsoft LONG type to C long
SIZE_T = ctypes.c_ulong # Map Microsoft SIZE_T type to C long
ULONG_PTR = ctypes.c_ulong # Map Microsoft ULONG_PTR to C long
LPTSTR = ctypes.c_char_p # Map Microsoft LPTSTR to a pointer to a string
LPCSTR = ctypes.c_char_p  # Map Microsoft LPCTSTR to a pointer to a string
ULARGE_INTEGER = ctypes.c_ulonglong # Map Microsoft ULARGE_INTEGER to 64 bit int
DWORDLONG = ctypes.c_ulonglong # Map Microsoft DWORDLONG to 64 bit int

# Microsoft Constants
TH32CS_SNAPTHREAD = ctypes.c_ulong(0x00000004) # Create a snapshot of all threads
TH32CS_SNAPPROCESS = ctypes.c_ulong(0x00000002) # Create a snapshot of a process
TH32CS_SNAPHEAPLIST = ctypes.c_ulong(0x00000001) # Create a snapshot of a processes heap
INVALID_HANDLE_VALUE = -1
THREAD_SUSPEND_RESUME = ctypes.c_ulong(0x0002)
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_AND_TERMINATE = PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION
ERROR_ALREADY_EXISTS = 183
SYNCHRONIZE = 0x00100000L
WAIT_FAILED = 0xFFFFFFFF
WAIT_OBJECT_0 = 0x00000000L
WAIT_ABANDONED = 0x00000080L
CE_FULL_PERMISSIONS = ctypes.c_ulong(0xFFFFFFFF)
NORMAL_PRIORITY_CLASS = ctypes.c_ulong(0x00000020)
HIGH_PRIORITY_CLASS = ctypes.c_ulong(0x00000080)

# How many times to attempt sleeping/resuming thread or proces
# before giving up with failure
ATTEMPT_MAX = 10 

# Key Functions
# Maps Microsoft API calls to more convenient name for internal use
# Also abstracts the linking library for each function for more portability

# Load the Functions that have a common library between desktop and CE
#_suspendThread = kerneldll.SuspendThread # Puts a thread to sleep
# This workaround is needed to keep the Python Global Interpreter Lock (GIL)
# Normal ctypes CFUNCTYPE or WINFUNCTYPE prototypes will release the GIL
# Which causes the process to infinitely deadlock
# The downside to this method, is that a ValueError Exception is always thrown
_suspendThreadProto = ctypes.PYFUNCTYPE(DWORD)
def _suspendThreadErrCheck(result, func, args):
  return result
_suspendThreadErr = _suspendThreadProto(("SuspendThread", kerneldll))
_suspendThreadErr.errcheck = _suspendThreadErrCheck

def _suspendThread(handle):
  result = 0
  try:
    result = _suspendThreadErr(handle)
  except ValueError:
    pass
  return result
  
_resumeThread = kerneldll.ResumeThread # Resumes Thread execution
_openProcess = kerneldll.OpenProcess # Returns Process Handle
_createProcess = kerneldll.CreateProcessW # Launches new process
_currentThreadId = kerneldll.GetCurrentThreadId # Returns the ThreadID of the current thread

_processExitCode = kerneldll.GetExitCodeProcess # Gets Process Exit code
_terminateProcess = kerneldll.TerminateProcess # Kills a process
_closeHandle = kerneldll.CloseHandle # Closes any(?) handle object
_getLastError = kerneldll.GetLastError # Gets last error number of last error
_waitForSingleObject = kerneldll.WaitForSingleObject # Waits to acquire mutex
_createMutex = kerneldll.CreateMutexW # Creates a Mutex, Unicode version
_releaseMutex = kerneldll.ReleaseMutex # Releases mutex

_freeDiskSpace = kerneldll.GetDiskFreeSpaceExW # Determines free disk space


# Load CE Specific function
if MobileCE:
  # Uses kernel, but is slightly different on desktop
  _globalMemoryStatus = kerneldll.GlobalMemoryStatus
  
  # Things using toolhelp
  _createSnapshot = toolhelp.CreateToolhelp32Snapshot # Makes snapshot of threads 
  _closeSnapshot = toolhelp.CloseToolhelp32Snapshot # destroys a snapshot 
  _firstThread = toolhelp.Thread32First # Reads from Thread from snapshot
  _nextThread = toolhelp.Thread32Next # Reads next Thread from snapshot
  
  # Things using kernel
  # Windows CE uses thread identifiers and handles interchangably
  # Use internal ce method to handle this
  # _openThreadCE
  
  # Opens an existing Mutex
  # Does not exist on CE, lets just link to _createMutex since that will open regardless
  _openMutex = _createMutex
  
  # Gets CPU time data for a thread
  # This is used by _processTimesCE
  _threadTimes = kerneldll.GetThreadTimes 

  # Non-Supported functions:
  # _processTimes, there is no tracking of this on a process level
  # _processMemory, CE does not track memory usage
  # These must be handled specifically
  
  # Heap functions only needed on CE for getting memory info
  _heapListFirst = toolhelp.Heap32ListFirst # Initializes Heap List
  _heapListNext = toolhelp.Heap32ListNext # Iterates through the heap list
  _heapFirst = toolhelp.Heap32First # Initializes Heap Entry
  _heapNext = toolhelp.Heap32Next # Iterates through the Heaps
  
  # Non-officially supported methods
  _getCurrentPermissions = kerneldll.GetCurrentPermissions
  _setProcessPermissions = kerneldll.SetProcPermissions
# Load the Desktop Specific functions
else:
  # These are in the kernel library on the desktop
  _openThread = kerneldll.OpenThread # Returns Thread Handle
  _createSnapshot = kerneldll.CreateToolhelp32Snapshot # Makes snapshot of threads 
  _firstThread = kerneldll.Thread32First # Reads from Thread from snapshot
  _nextThread = kerneldll.Thread32Next # Reads next Thread from snapshot
  _openMutex = kerneldll.OpenMutexW # Opens an existing Mutex, Unicode Version
  _globalMemoryStatus = kerneldll.GlobalMemoryStatusEx # Gets global memory info
  
  # These process specific functions are only available on the desktop
  _processTimes = kerneldll.GetProcessTimes # Returns data about Process CPU use
  _processMemory = memdll.GetProcessMemoryInfo # Returns data on Process mem use
  

# Classes
# Python Class which is converted to a C struct
# It encapsulates Thread Data, and is used in
# Windows Thread calls
class _THREADENTRY32(ctypes.Structure): 
    _fields_ = [('dwSize', DWORD), 
                ('cntUsage', DWORD), 
                ('th32ThreadID', DWORD), 
                ('th32OwnerProcessID', DWORD),
                ('tpBasePri', LONG),
                ('tpDeltaPri', LONG),
                ('dwFlags', DWORD)]

# It encapsulates Thread Data, and is used in
# Windows Thread calls, CE Version
class _THREADENTRY32CE(ctypes.Structure): 
    _fields_ = [('dwSize', DWORD), 
                ('cntUsage', DWORD), 
                ('th32ThreadID', DWORD), 
                ('th32OwnerProcessID', DWORD),
                ('tpBasePri', LONG),
                ('tpDeltaPri', LONG),
                ('dwFlags', DWORD),
                ('th32AccessKey', DWORD),
                ('th32CurrentProcessID', DWORD)]



# Python Class which is converted to a C struct
# It encapsulates Time data, with a low and high number
# We use it to get Process times (user/system/etc.)
class _FILETIME(ctypes.Structure): 
    _fields_ = [('dwLowDateTime', DWORD), 
                ('dwHighDateTime', DWORD)]



# Python Class which is converted to a C struct
# It encapsulates data about a Processes 
# Memory usage. A pointer to the struct is passed
# to the Windows API
class _PROCESS_MEMORY_COUNTERS(ctypes.Structure): 
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


# Python Class which is converted to a C struct
# It encapsulates data about a heap space
# see http://msdn.microsoft.com/en-us/library/ms683443(VS.85).aspx
class _HEAPENTRY32(ctypes.Structure): 
    _fields_ = [('dwSize', SIZE_T), 
                ('hHandle', HANDLE), 
                ('dwAddress', ULONG_PTR), 
                ('dwBlockSize', SIZE_T),
                ('dwFlags', DWORD),
                ('dwLockCount', DWORD),
                ('dwResvd', DWORD),
                ('th32ProcessID', DWORD),
                ('th32HeapID', ULONG_PTR)]
                
# Python Class which is converted to a C struct
# It encapsulates data about a processes heaps
# see http://msdn.microsoft.com/en-us/library/ms683449(VS.85).aspx
class _HEAPLIST32(ctypes.Structure): 
    _fields_ = [('dwSize', SIZE_T), 
                ('th32ProcessID', DWORD), 
                ('th32HeapID', ULONG_PTR), 
                ('dwFlags', DWORD)]

# Python Class which is converted to a C struct
# It encapsulates data about a newly created process
# see http://msdn.microsoft.com/en-us/library/ms684873(VS.85).aspx
class _PROCESS_INFORMATION(ctypes.Structure): 
    _fields_ = [('hProcess', HANDLE), 
                ('hThread', HANDLE), 
                ('dwProcessId', DWORD), 
                ('dwThreadId', DWORD)]
                 

# Python Class which is converted to a C struct
# It encapsulates data about a Processes 
# after it is created
# see http://msdn.microsoft.com/en-us/library/ms686331(VS.85).aspx
class _STARTUPINFO(ctypes.Structure): 
    _fields_ = [('cb', DWORD), 
                ('lpReserved', LPTSTR), 
                ('lpDesktop', LPTSTR), 
                ('lpTitle', LPTSTR),
                ('dwX', DWORD),
                ('dwY', DWORD),
                ('dwXSize', DWORD),
                ('dwYSize', DWORD),
                ('dwXCountChars', DWORD),
                ('dwYCountChars', DWORD),
                ('dwFillAttribute', DWORD),
                ('dwFlags', DWORD),
                ('wShowWindow', DWORD),
                ('cbReserved2', WORD),
                ('lpReserved2', WORD),
                ('hStdInput', HANDLE),
                ('hStdOutput', HANDLE),
                ('hStdError', HANDLE)]

# Python Class which is converted to a C struct
# It encapsulates data about global memory
# This version is for Windows Desktop, and is not limited to 4 gb of ram
# see http://msdn.microsoft.com/en-us/library/aa366770(VS.85).aspx
class _MEMORYSTATUSEX(ctypes.Structure): 
    _fields_ = [('dwLength', DWORD), 
                ('dwMemoryLoad', DWORD), 
                ('ullTotalPhys', DWORDLONG), 
                ('ullAvailPhys', DWORDLONG),
                ('ullTotalPageFile', DWORDLONG),
                ('ullAvailPageFile', DWORDLONG),
                ('ullTotalVirtual', DWORDLONG),
                ('ullAvailVirtual', DWORDLONG),
                ('ullAvailExtendedVirtual', DWORDLONG)]        
 
# Python Class which is converted to a C struct
# It encapsulates data about global memory
# This version is for WinCE (< 4gb ram)
# see http://msdn.microsoft.com/en-us/library/bb202730.aspx
class _MEMORYSTATUS(ctypes.Structure): 
   _fields_ = [('dwLength', DWORD), 
               ('dwMemoryLoad', DWORD), 
               ('dwTotalPhys', DWORD), 
               ('dwAvailPhys', DWORD),
               ('dwTotalPageFile', DWORD),
               ('dwAvailPageFile', DWORD),
               ('dwTotalVirtual', DWORD),
               ('dwAvailVirtual', DWORD)]          
                                
# Exceptions

class DeadThread(Exception):
  """Gets thrown when a Tread Handle cannot be opened"""
  pass


class DeadProcess(Exception):
  """Gets thrown when a Process Handle cannot be opened. Eventually a DeadThread will get escalated to DeadProcess"""
  pass


class FailedMutex(Exception):
  """Gets thrown when a Mutex cannot be created, opened, or released"""
  pass


# Global variables

# For each Mutex, record the lock count to properly release
_MutexLockCount = {}
   
# High level functions

# Returns list with the Thread ID of all threads associated with the PID
def getProcessThreads(PID):
  """
  <Purpose>
    Many of the Windows functions for altering processes and threads require
    thread-based handles, as opposed to process based, so this function
    gets all of the threads associated with a given process
  
  <Arguments>
    PID:
           The Process Identifier number for which the associated threads should be returned
  
  <Returns>
    Array of Thread Identifiers, these are not thread handles
  """
  # Mobile requires different structuer
  if MobileCE:
    threadClass = _THREADENTRY32CE
  else:
    threadClass = _THREADENTRY32
    
  threads = [] # List object for threads
  currentThread = threadClass() # Current Thread Pointer
  currentThread.dwSize = ctypes.sizeof(threadClass)
  
  # Create Handle to snapshot of all system threads
  handle = _createSnapshot(TH32CS_SNAPTHREAD, 0)
  
  # Check if handle was created successfully
  if handle == INVALID_HANDLE_VALUE:
    _closeHandle( handle )
    return []
  
  # Attempt to read snapshot
  if not _firstThread( handle, ctypes.pointer(currentThread)):
    _closeHandle( handle )
    return []
  
  # Loop through threads, check for threads associated with the right process
  moreThreads = True
  while (moreThreads):
    # Check if current thread belongs to the process were looking for
    if currentThread.th32OwnerProcessID == ctypes.c_ulong(PID).value: 
      threads.append(currentThread.th32ThreadID)
    moreThreads = _nextThread(handle, ctypes.pointer(currentThread))
  
  # Cleanup snapshot
  if MobileCE:
    _closeSnapshot(handle)
  _closeHandle(handle)
    
  return threads  



# Returns a handle for ThreadID  
def getThreadHandle(ThreadID):
  """
    <Purpose>
      Returns a thread handle for a given thread identifier. This is useful
      because a thread identified cannot be used directly for most operations.
  
    <Arguments>
      ThreadID:
             The Thread Identifier, for which a handle is returned
  
   <Side Effects>
     If running on a mobile CE platform, execution permissions will be elevated.
     closeThreadHandle must be called before getThreadHandle is called again,
     or permissions will not be set to their original level.
     
    <Exceptions>
      DeadThread on bad parameters or general error
  
    <Returns>
      Thread Handle
    """
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    handle = _openThreadCE(ThreadID)
  else:
    # Open handle to thread
    handle = _openThread(THREAD_SUSPEND_RESUME, 0, ThreadID)
  
  # Check for a successful handle
  if handle: 
    return handle
  else: # Raise exception on failure
    raise DeadThread, "Error opening thread handle! ThreadID: " + str(ThreadID) + " Error Str: " + str(ctypes.WinError())  


# Closes a thread handle
def closeThreadHandle(TheadHandle):
  """
    <Purpose>
      Closes a given thread handle.
  
    <Arguments>
      ThreadHandle:
             The Thread handle which is closed
    """
    
  # Check if it is CE
  if MobileCE:
    # Opening a thread raises permissions,
    # so we need to revert to default
    _revertPermissions();
  
  # Close thread handle
  _closeHandle(TheadHandle)
    
    
# Suspend a thread with given ThreadID
def suspendThread(ThreadID):
  """
    <Purpose>
      Suspends the execution of a thread.
      Will not execute on currently executing thread.
  
    <Arguments>
      ThreadID:
             The thread identifier for the thread to be suspended.
  
    <Exceptions>
      DeadThread on bad parameters or general error.
  
    <Side Effects>
      Will suspend execution of the thread until resumed or terminated.
  
    <Returns>
      True on success, false on failure
    """
  # Check if it is the currently executing thread, and return
  if ThreadID == _currentThreadId():
    return True
      
  # Open handle to thread
  handle = getThreadHandle(ThreadID)
  
  # Try to suspend thread, save status of call
  status = _suspendThread(handle)
  
  # Close thread handle
  closeThreadHandle(handle)
  
  # -1 is returned on failure, anything else on success
  # Translate this to True and False
  return (not status == -1)



# Resume a thread with given ThreadID
def resumeThread(ThreadID):
  """
    <Purpose>
      Resumes the execution of a thread.
  
    <Arguments>
      ThreadID:
             The thread identifier for the thread to be resumed
  
    <Exceptions>
      DeadThread on bad parameter or general error.
  
    <Side Effects>
      Will resume execution of a thread.
  
    <Returns>
      True on success, false on failure
    """
    
  # Get thread Handle
  handle = getThreadHandle(ThreadID)
  
  # Attempt to resume thread, save status of call
  val = _resumeThread(handle)
  
  # Close Thread Handle
  closeThreadHandle(handle)
  
  # -1 is returned on failure, anything else on success
  # Translate this to True and False
  return (not val == -1)



# Suspend a process with given PID
def suspendProcess(PID):
  """
  <Purpose>
    Instead of manually getting a list of threads for a process and individually
    suspending each, this function will do the work transparently.
  
  <Arguments>
    PID:
      The Process Identifier number to be suspended.
  
  <Side Effects>
    Suspends the given process indefinitely.
  
  <Returns>
    True on success, false on failure
  """
  
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
def resumeProcess(PID):
  """
  <Purpose>
    Instead of manually resuming each thread in a process, this functions
    handles that transparently.
  
  <Arguments>
    PID:
      The Process Identifier to be resumed.
  
  <Side Effects>
    Resumes thread execution
  
  <Returns>
    True on success, false on failure
  """
  
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
def timeoutProcess(PID, stime):
  """
  <Purpose>
    Calls suspendProcess and resumeProcess with a specified period of sleeping.
  
  <Arguments>
    PID:
      The process identifier to timeout execution.
    stime:
      The time period in seconds to timeout execution.
  
  <Exceptions>
    DeadProcess if there is a critical problem sleeping or resuming a thread.
    
  <Side Effects>
    Timeouts the execution of the process for specified interval.
    The timeout period is blocking, and will cause a general timeout in the
    calling thread.
    
  <Returns>
    True of success, false on failure.
  """
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
def getProcessHandle(PID):
  """
  <Purpose>
    Get a process handle for a specified process identifier
  
  <Arguments>
    PID:
      The process identifier for which a handle is returned.
  
  <Exceptions>
    DeadProcess on bad parameter or general error.
  
  <Returns>
    Process handle
  """
  
  # Get handle to process
  handle = _openProcess( PROCESS_QUERY_AND_TERMINATE, 0, PID)
  
  # Check if we successfully got a handle
  if handle:
    return handle
  else: # Raise exception on failure
    raise DeadProcess, "Error opening process handle! Process ID: " + str(PID) + " Error Str: " + str(ctypes.WinError())


# Launches a new process
def launchProcess(application,cmdline = None, priority = NORMAL_PRIORITY_CLASS):
  """
  <Purpose>
    Launches a new process.
  
  <Arguments>
    application:
      The path to the application to be started
    cmdline:
      The command line parameters that are to be used
    priority
      The priority of the process. See NORMAL_PRIORITY_CLASS and HIGH_PRIORITY_CLASS
      
  <Side Effects>
    A new process is created
  
  <Returns>
    Process ID on success, None on failure.
  """
  # Create struct to hold process info
  processInfo = _PROCESS_INFORMATION()
  processInfoAddr = ctypes.pointer(processInfo)
  
  # Determine what is the cmdline Parameter
  if not (cmdline == None):
    cmdlineParam = unicode(cmdline)
  else:
    cmdlineParam = None
  
  # Adjust for CE
  if MobileCE:
    # Not Supported on CE
    priority = 0
    windowInfoAddr = 0
    # Always use absolute path
    application = os.path.abspath(application) 
  else:
    # Create struct to hold window info
    windowInfo = _STARTUPINFO()
    windowInfoAddr = ctypes.pointer(windowInfo)
  
  # Lauch process, and save status
  status = _createProcess(
    unicode(application), 
    cmdlineParam,
    None,
    None,
    False,
    priority,
    None,
    None,
    windowInfoAddr,
    processInfoAddr)
  
  # Did we succeed?
  if status:
    # Close handles that we don't need
    _closeHandle(processInfo.hProcess)
    _closeHandle(processInfo.hThread)
    
    # Return PID
    return processInfo.dwProcessId
  else:
    return None

# Helper function to launch a python script with some parameters
def launchPythonScript(script, params=""):
  """
  <Purpose>
    Launches a python script with parameters
  
  <Arguments>
    script:
      The python script to be started
    params:
      A string command line parameter for the script
      
  <Side Effects>
    A new process is created
  
  <Returns>
    Process ID on success, None on failure.
  """
  
  # Get all repy constants
  import repy_constants
  
  # Create python command line string
  # Use absolute path for compatibility
  cmd = repy_constants.PYTHON_DEFAULT_FLAGS + "\"" + os.path.abspath(script) + "\" " + params
  
  # Launch process and store return value
  retval = launchProcess(repy_constants.PATH_PYTHON_INSTALL,cmd)
  
  return retval


# Kill a process with specified PID
def killProcess(PID):
  """
  <Purpose>
    Terminates a process.
  
  <Arguments>
    PID:
      The process identifier to be killed.
  
  <Exceptions>
    DeadProcess on bad parameter or general error.
  
  <Side Effects>
    Terminates the process
  
  <Returns>
    True on success, false on failure.
  """
  
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
      raise DeadProcess, "Failed to kill process! Process ID: " + str(PID) + " Error Str: " + str(ctypes.WinError())
  
    # Increment attempt count
    attempt = attempt + 1 
  
    # Attempt to terminate process
    # 0 is return code for failure, convert it to True/False
    dead = not 0 == _terminateProcess(handle, 0)
  
  # Close Process Handle
  _closeHandle(handle)
  
  return True



# Get information about a process CPU use times
def processTimes(PID):
  """
  <Purpose>
    Gets information about a processes CPU time utilization.
    Because Windows CE does not keep track of this information at a process level,
    if a thread terminates (belonging to the PID), then it is possible for the 
    KernelTime and UserTime to be lower than they were previously.
  
  <Arguments>
    PID:
      The process identifier about which the information is returned
  
  <Exceptions>
    DeadProcess on bad parameter or general error.
  
  <Returns>
    Dictionary with the following indices:
    CreationTime: the time at which the process was created
    KernelTime: the execution time of the process in the kernel
    UserTime: the time spent executing user code
  """
  
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    return _processTimesCE(PID)
  
  # Open process handle
  handle = getProcessHandle(PID)
  
  # Create all the structures needed to make API Call
  creationTime = _FILETIME()
  exitTime = _FILETIME()
  kernelTime = _FILETIME()
  userTime = _FILETIME()
  
  # Pass all the structures as pointers into processTimes
  _processTimes(handle, ctypes.pointer(creationTime), ctypes.pointer(exitTime), ctypes.pointer(kernelTime), ctypes.pointer(userTime))
  
  # Close Process Handle
  _closeHandle(handle)
  
  # Extract the values from the structures, and return then in a dictionary
  return {"CreationTime":creationTime.dwLowDateTime,"KernelTime":kernelTime.dwLowDateTime,"UserTime":userTime.dwLowDateTime}



# Get the exit code of a process
def processExitCode(PID):
  """
  <Purpose>
    Get the exit code of a process
  
  <Arguments>
    PID:
      The process identifier for which the exit code is returned.
  
  <Returns>
    The process exit code, or 0 on failure.
  """
  
  try:
    # Get process handle
    handle = getProcessHandle(PID)
  except DeadProcess:
    # Process is likely dead, so give anything other than 259
    return 0
 
  # Store the code, 0 by default
  code = ctypes.c_int(0)
  
  # Pass in code as a pointer to store the output
  _processExitCode(handle, ctypes.pointer(code))
  
  # Close the Process Handle
  _closeHandle(handle)
  return code.value



# Get information on process memory use
def processMemoryInfo(PID):
  """
  <Purpose>
    Get information about a processes memory usage.
    On Windows CE, all of the dictionary indices will return the same
    value. This is due to the imprecision of CE's memory tracking,
    and all of the indices are only returned for compatibility reasons.
  
  <Arguments>
    PID:
      The process identifier for which memory info is returned
  
  <Exceptions>
    DeadProcess on bad parameters or general error.
  
  <Returns>
    Dictionary with memory data associated with description.
  """
  
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    return _processMemoryInfoCE(PID)
    
  # Open process Handle
  handle = getProcessHandle(PID)
  
  # Define structure to hold memory data
  meminfo = _PROCESS_MEMORY_COUNTERS()
  
  # Pass pointer to meminfo to processMemory to store the output
  _processMemory(handle, ctypes.pointer(meminfo), ctypes.sizeof(_PROCESS_MEMORY_COUNTERS))
  
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
  """
  <Purpose>
    Creates and returns a handle to a mutex
  
  <Arguments>
    name:
      The name of the mutex to be created
  
  <Exceptions>
    FailedMutex on bad parameters or failure to create mutex.
  
  <Side Effects>
    Creates a global mutex and retains control.
  
  <Returns>
    handle to the mutex.
  """
  
  # Attempt to create Mutex
  handle = _createMutex(None, 0, name)
  
  # Check for a successful handle
  if not handle == False: 
    # Set the lock count to 1
    _MutexLockCount[handle] = 1
    return handle
  else: # Raise exception on failure
    raise FailedMutex, (_getLastError(), "Error creating mutex! Mutex name: " + str(name) + " Error Str: " + str(ctypes.WinError()))



# Opens and returns a handle to a Mutex
def openMutex(name):
  """
  <Purpose>
    Opens a pre-existing mutex. Does not get control of it.
  
  <Arguments>
    name:
      The name of the mutex to open.
  
  <Exceptions>
    FailedMutex on bad parameters or failure to open the mutex.
  
  <Returns>
    Handle to the mutex
  """
  
  # Attempt to create Mutex
  handle = _openMutex(SYNCHRONIZE, 0, name)
  
  # Check for a successful handle
  if not handle == False: 
    # Set the lock count to 1
    _MutexLockCount[handle] = 1
    return handle
  else: # Raise exception on failure
    raise FailedMutex, (_getLastError(), "Error opening mutex! Mutex name: " + str(name) + " Error Str: " + str(ctypes.WinError()))



# Waits for specified interval to acquire Mutex
# time should be in milliseconds
def acquireMutex(handle, time):
  """
  <Purpose>
    Acquires exclusive control of a mutex
  
  <Arguments>
    handle:
      Handle to a mutex object
    time:
      the time to wait in milliseconds to get control of the mutex
  
  <Side Effects>
    If successful, the calling thread had exclusive control of the mutex
  
  <Returns>
    True if the mutex is acquired, false otherwise.
  """
  
  # Wait up to time to acquire lock, fail otherwise
  val = _waitForSingleObject(handle, time)
  
  # Update lock count
  _MutexLockCount[handle] += 1
  
  # WAIT_OBJECT_0 is returned on success, other on failure
  return (val == WAIT_OBJECT_0) or (val == WAIT_ABANDONED)



# Releases a mutex
def releaseMutex(handle):
  """
  <Purpose>
    Releases control of a mutex
  
  <Arguments>
    handle:
      Handle to the mutex object to be release
  
  <Exceptions>
    FailedMutex if a general error is occurred when releasing the mutex.
    This is not raised if the mutex is not owned, and a release is attempted.
  
  <Side Effects>
    If controlled previous to calling, then control will be given up
  
  <Returns>
    None.
  """
  
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
        raise FailedMutex, (_getLastError(), "Error releasing mutex! Mutex id: " + str(handle) + " Error Str: " + str(ctypes.WinError()))
    except FailedMutex, e:
      if (e[0] == 288): # 288 is for non-owned mutex, which is ok
        pass
      else:
        raise


# Windows CE Stuff
# Internal function, not public

# Get information about a process CPU use times
# Windows CE does not have a GetProcessTimes function, so we will emulate it
def _processTimesCE(PID):
  # Get List of threads related to Process
  threads = getProcessThreads(PID)
  
  # Create all the structures needed to make API Call
  creationTime = _FILETIME()
  exitTime = _FILETIME()
  kernelTime = _FILETIME()
  userTime = _FILETIME()
  
  # Create counters for each category
  # Only adds the "low date time" (see _FILETIME()), since thats what we return
  creationTimeSum = 0
  exitTimeSum = 0 # We don't return this, but we keep it anyways
  kernelTimeSum = 0
  userTimeSum = 0
  
  # Get the process times for each thread
  for t in threads:
    # Open handle to thread
    handle = getThreadHandle(t)
  
    # Pass all the structures as pointers into threadTimes
    _threadTimes(handle, ctypes.pointer(creationTime), ctypes.pointer(exitTime), ctypes.pointer(kernelTime), ctypes.pointer(userTime))
  
    # Close thread Handle
    closeThreadHandle(handle)
    
    # Update all the counters
    creationTimeSum += creationTime.dwLowDateTime
    exitTimeSum += exitTime.dwLowDateTime
    kernelTimeSum += kernelTime.dwLowDateTime
    userTimeSum += userTime.dwLowDateTime
  
  # Return the proper values in a dictionaries
  return {"CreationTime":creationTimeSum,"KernelTime":kernelTimeSum,"UserTime":userTimeSum}



# Windows CE does not have a GetProcessMemoryInfo function,
# so memory usage may be more inaccurate
# We iterate over all of the process's heap spaces, and tally up the
# total size, and return that value for all types of usage
def _processMemoryInfoCE(PID):
  heapSize = 0 # Keep track of heap size
  heapList = _HEAPLIST32() # List of heaps
  heapEntry = _HEAPENTRY32() # Current Heap entry
  
  heapList.dwSize = ctypes.sizeof(_HEAPLIST32)
  heapEntry.dwSize = ctypes.sizeof(_HEAPENTRY32)
  
  # Create Handle to snapshot of all system threads
  handle = _createSnapshot(TH32CS_SNAPHEAPLIST, PID)
  
  # Check if handle was created successfully
  if handle == INVALID_HANDLE_VALUE:
    return {}
  
  # Attempt to read snapshot
  if not _heapListFirst( handle, ctypes.pointer(heapList)):
    _closeSnapshot(handle)
    _closeHandle(handle)
    return {}
  
  # Loop through threads, check for threads associated with the right process
  moreHeaps = True
  while (moreHeaps):
    
    # Check if there is a heap entry here
    if _heapFirst(handle, ctypes.pointer(heapEntry), heapList.th32ProcessID, heapList.th32HeapID):
      
      # Loop through available heaps
      moreEntries = True
      while moreEntries:
        # Increment the total heap size by the current heap size
        heapSize += heapEntry.dwBlockSize
        
        heapEntry.dwSize = ctypes.sizeof(_HEAPENTRY32)
        moreEntries = _heapNext(handle, ctypes.pointer(heapEntry)) # Go to next Heap entry
    
    heapList.dwSize = ctypes.sizeof(_HEAPLIST32)
    moreHeaps = _heapListNext(handle, ctypes.pointer(heapList)) # Go to next Heap List
  
  # Cleanup snapshot
  _closeSnapshot(handle)
  _closeHandle(handle)
  
  # Since we only have one value, return that for all different possible sets
  return {'PageFaultCount':heapSize,
          'PeakWorkingSetSize':heapSize,
          'WorkingSetSize':heapSize,
          'QuotaPeakPagedPoolUsage':heapSize,
          'QuotaPagedPoolUsage':heapSize,
          'QuotaPeakNonPagedPoolUsage':heapSize,
          'QuotaNonPagedPoolUsage':heapSize,
          'PagefileUsage':heapSize,
          'PeakPagefileUsage':heapSize}  


# Windows CE does not have a separate handle for threads
# Since handles and identifiers are interoperable, just return the ID
# Set process permissions higher or else this will fail
def _openThreadCE(ThreadID):
	# Save original permissions
	global _originalPermissionsCE
	_originalPermissionsCE = _getProcessPermissions()
	
	# Get full system control
	_setCurrentProcPermissions(CE_FULL_PERMISSIONS)
	
	return ThreadID

# Sets the permission level of the current process
def _setCurrentProcPermissions(permission):
	_setProcessPermissions(permission)

# Global variable to store permissions
_originalPermissionsCE = None

# Returns the permission level of the current process
def _getProcessPermissions():
	return _getCurrentPermissions()

# Reverts permissions to original
def _revertPermissions():
	global _originalPermissionsCE
	if not _originalPermissionsCE == None:
		_setCurrentProcPermissions(_originalPermissionsCE)

## Resource Determining Functions
# For number of CPU's check the %NUMBER_OF_PROCESSORS% Environment variable 


# Determines available and used disk space
def diskUtil(directory):
  """"
  <Purpose>
    Gets information about disk utilization, and free space.
  
  <Arguments>
    directory:
      The directory to be queried. This can be a folder, or a drive root.
      If set to None, then the current directory will be used.
  
  <Exceptions>
    EnvironmentError on bad parameter.
  
  <Returns>
    Dictionary with the following indices:
    bytesAvailable: The number of bytes available to the current user
    totalBytes: The total number of bytes
    freeBytes: The total number of free bytes
  """  
  # Define values that need to be passed to the function
  bytesFree = ULARGE_INTEGER(0)
  totalBytes = ULARGE_INTEGER(0)
  totalFreeBytes = ULARGE_INTEGER(0)
  
  # Allow for a Null parameter
  dirchk = None
  if not directory == None:
    dirchk = unicode(directory)
  
  status = _freeDiskSpace(dirchk, ctypes.pointer(bytesFree), ctypes.pointer(totalBytes), ctypes.pointer(totalFreeBytes))
  
  print bytesFree, totalBytes, totalFreeBytes
    
  # Check if we succeded
  if status == 0:
    raise EnvironmentError("Failed to determine free disk space: Directory: "+directory)
  
  return {"bytesAvailable":bytesFree.value,"totalBytes":totalBytes.value,"freeBytes":totalFreeBytes.value}

# Get global memory information
def globalMemoryInfo():
  """"
  <Purpose>
    Gets information about memory utilization
  
  <Exceptions>
    EnvironmentError on general error.
  
  <Returns>
    Dictionary with the following indices:
    load: The percentage of memory in use
    totalPhysical: The total amount of physical memory
    availablePhysical: The total free amount of physical memory
    totalPageFile: The current size of the committed memory limit, in bytes. This is physical memory plus the size of the page file, minus a small overhead.
    availablePageFile: The maximum amount of memory the current process can commit, in bytes.
    totalVirtual: The size of the user-mode portion of the virtual address space of the calling process, in bytes
    availableVirtual: The amount of unreserved and uncommitted memory currently in the user-mode portion of the virtual address space of the calling process, in bytes.
  """
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    return _globalMemoryInfoCE()
    
  # Initialize the data structure
  memInfo = _MEMORYSTATUSEX() # Memory usage ints
  memInfo.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
  
  # Make the call, save the status
  status = _globalMemoryStatus(ctypes.pointer(memInfo))
 
  # Check if we succeded
  if status == 0:
    raise EnvironmentError("Failed to get global memory info!")

  # Return Dictionary
  return {"load":memInfo.dwMemoryLoad,
  "totalPhysical":memInfo.ullTotalPhys,
  "availablePhysical":memInfo.ullAvailPhys,
  "totalPageFile":memInfo.ullTotalPageFile,
  "availablePageFile":memInfo.ullAvailPageFile,
  "totalVirtual":memInfo.ullTotalVirtual,
  "availableVirtual":memInfo.ullAvailVirtual}
    
def _globalMemoryInfoCE():
  # Initialize the data structure
  memInfo = _MEMORYSTATUS() # Memory usage ints
  memInfo.dwLength = ctypes.sizeof(_MEMORYSTATUS)
  
  # Make the call
  _globalMemoryStatus(ctypes.pointer(memInfo))
  
  # Return Dictionary
  return {"load":memInfo.dwMemoryLoad,
  "totalPhysical":memInfo.dwTotalPhys,
  "availablePhysical":memInfo.dwAvailPhys,
  "totalPageFile":memInfo.dwTotalPageFile,
  "availablePageFile":memInfo.dwAvailPageFile,
  "totalVirtual":memInfo.dwTotalVirtual,
  "availableVirtual":memInfo.dwAvailVirtual}
  
  
  