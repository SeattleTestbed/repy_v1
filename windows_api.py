# Armon Dadgar
# 
# Creates python interface for windows api calls that are required 
#
# According to MSDN most of these calls are Windows 2K Pro and up
# Trying to replace the win32* stuff using ctypes

from ctypes import * 
import os
import time

# Main Libraries
kerneldll = windll.kernel32 
memdll = windll.psapi

# Types
DWORD = c_ulong
HANDLE = c_ulong
LONG = c_long
SIZE_T = c_ulong

# Constants
TH32CS_SNAPTHREAD = c_ulong(0x00000004)
INVALID_HANDLE_VALUE = -1
THREAD_SUSPEND_RESUME = c_ulong(0x0002)
ATTEMPT_MAX = 10
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_AND_TERMINATE = PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION

# Key Functions
_createSnapshot = kerneldll.CreateToolhelp32Snapshot # Makes snapshot of threads 
_openThread = kerneldll.OpenThread
_firstThread = kerneldll.Thread32First
_nextThread = kerneldll.Thread32Next
_suspendThread = kerneldll.SuspendThread
_resumeThread = kerneldll.ResumeThread
_openProcess = kerneldll.OpenProcess
_processTimes = kerneldll.GetProcessTimes
_processMemory = memdll.GetProcessMemoryInfo
_processExitCode = kerneldll.GetExitCodeProcess
_terminateProcess = kerneldll.TerminateProcess
_closeHandle = kerneldll.CloseHandle # Closes any(?) handle object
_getLastError = kerneldll.GetLastError

# Classes
class _THREADENTRY32(Structure): 
    _fields_ = [('dwSize', DWORD), 
                ('cntUsage', DWORD), 
                ('th32ThreadID', DWORD), 
                ('th32OwnerProcessID', DWORD),
                ('tpBasePri', LONG),
				('tpDeltaPri', LONG),
				('dwFlags', DWORD)]

class _FILETIME(Structure): 
    _fields_ = [('dwLowDateTime', DWORD), 
                ('dwHighDateTime', DWORD)]

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
		if currentThread.th32OwnerProcessID == PID: 
			threads.append(currentThread.th32ThreadID)
		moreThreads = _nextThread(handle, pointer(currentThread))
	
	# Cleanup snapshot
	_closeHandle(handle)
	
	return threads	

# Returns a handle for ThreadID	
def getThreadHandle (ThreadID):
	return _openThread(THREAD_SUSPEND_RESUME, 0, ThreadID)
	
# Suspend a thread with given ThreadID
def suspendThread (ThreadID):
	handle = getThreadHandle(ThreadID)
	val = _suspendThread(handle)
	_closeHandle(handle)
	return (not val == -1)

# Resume a thread with given ThreadID
def resumeThread (ThreadID):
	handle = getThreadHandle(ThreadID)
	val = _resumeThread(handle)
	_closeHandle(handle)
	return (not val == -1)

# Suspend a process with given PID
def suspendProcess (PID):
	threads = getProcessThreads(PID)
	for t in threads:
		sleep = False # Loop until thread sleeps
		attempt = 0
		while not sleep:
			if (attempt > ATTEMPT_MAX):
				raise Exception, "Failed to sleep thread while sleeping process! " + "Error Str: " + str(WinError())
			attempt = attempt + 1
			sleep = suspendThread(t)

# Resume a process with given PID
def resumeProcess (PID):
	threads = getProcessThreads(PID)
	for t in threads:
		wake = False # Loop until thread wakes up
		attempt = 0
		while not wake: 
			if (attempt > ATTEMPT_MAX):
				raise Exception, "Failed to resume thread while resuming process! " + "Error Str: " + str(WinError())
			attempt = attempt + 1
			wake = resumeThread(t)
		
# Suspends a process and restarts after a given time interval
def timeoutProcess (PID, stime):
	suspendProcess(PID)
	time.sleep (stime)
	resumeProcess(PID)

# Gets a process handle
def getProcessHandle (PID):
	return _openProcess( PROCESS_QUERY_AND_TERMINATE, 0, PID)
		
# Kill a process with specified PID
def killProcess (PID):
	handle = getProcessHandle(PID)
	dead = False
	attempt = 0
	while not dead:
		if (attempt > ATTEMPT_MAX):
			raise Exception, "Failed to kill process! " + "Error Str: " + str(WinError())
		attempt = attempt + 1
		dead = not 0 == _terminateProcess(handle, 0)
	_closeHandle(handle)
			
# Get information about a process CPU use times
def processTimes (PID):
	handle = getProcessHandle(PID)
	creationTime = _FILETIME()
	exitTime = _FILETIME()
	kernelTime = _FILETIME()
	userTime = _FILETIME()
	_processTimes(handle, pointer(creationTime), pointer(exitTime), pointer(kernelTime), pointer(userTime))
	_closeHandle(handle)
	return {"CreationTime":creationTime.dwLowDateTime,"KernelTime":kernelTime.dwLowDateTime,"UserTime":userTime.dwLowDateTime}
	
# Get the exit code of a process
def processExitCode (PID):
	handle = getProcessHandle(PID)
	code = c_int(0)
	_processExitCode(handle, pointer(code))
	_closeHandle(handle)
	return code.value
	
# Get information on process memory use
def processMemoryInfo (PID):
	handle = getProcessHandle(PID)
	meminfo = _PROCESS_MEMORY_COUNTERS()
	_processMemory(handle, pointer(meminfo), sizeof(_PROCESS_MEMORY_COUNTERS))
	_closeHandle(handle)
	return {'PageFaultCount':meminfo.PageFaultCount,
	        'PeakWorkingSetSize':meminfo.PeakWorkingSetSize,
	        'WorkingSetSize':meminfo.WorkingSetSize,
	        'QuotaPeakPagedPoolUsage':meminfo.QuotaPeakPagedPoolUsage,
	        'QuotaPagedPoolUsage':meminfo.QuotaPagedPoolUsage,
	        'QuotaPeakNonPagedPoolUsage':meminfo.QuotaPeakNonPagedPoolUsage,
	        'QuotaNonPagedPoolUsage':meminfo.QuotaNonPagedPoolUsage,
	        'PagefileUsage':meminfo.PagefileUsage,
	        'PeakPagefileUsage':meminfo.PeakPagefileUsage}	