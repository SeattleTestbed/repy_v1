""" 
Author: Justin Cappos

Start Date: July 1st, 2008

Description:
Handles exiting and killing all threads, tracking CPU / Mem usage, etc.


"""


import threading
import os
import time

# needed for sys.stderr and windows Popen hackery
import sys

# print useful info when exiting...
import tracebackrepy

# used to get information about the system we're running on
import platform

# needed for signal numbers
import signal

import traceback

# I use this so that the safe module doesn't complain about us using open
myopen = open

# used to query status, etc.
# This may fail on Windows CE
try:
  import subprocess
  mobileNoSubprocess = False
except ImportError:
  # Set flag to avoid using subprocess
  mobileNoSubprocess = True 
  pass

# used for select (duh)
import select

# used for socket.error
import socket

# need for status retrieval
import statusstorage

# needed to check disk usage
import misc

# Get constants
import repy_constants

# These are used to determine uptime on BSD/Mac systems
import ctypes
import ctypes.util

# This prevents writes to the nanny's status information after we want to stop
statuslock = threading.Lock()

# This will fail on non-windows systems
try:
  import windows_api as windowsAPI
except:
  windowsAPI = None
  pass

# this indicates if we are exiting.   Wrapping in a list to prevent needing a
# global   (the purpose of this is described below)
statusexiting = [False]

# this will be a string that identifies us at a high level
ostype = None

# this will be more fine grained information about us (i.e. the raw data...)
osrealtype = None


class UnsupportedSystemException(Exception):
  pass





###################     Publicly visible functions   #######################

# prepare a socket so it behaves how we want
def preparesocket(socketobject):
  
  if ostype == 'Windows':
    # we need to set a timeout because on rare occasions Windows will block 
    # on recvmess with a bad socket.  This prevents it from locking the system.
    # We use select, so the timeout should never be actually used.

    # The actual value doesn't seem to matter, so I'll use 100 years
    socketobject.settimeout(60*60*24*365*100)

  elif ostype == 'Linux' or ostype == 'Darwin':
    # Linux seems not to care if we set the timeout, Mac goes nuts and refuses
    # to let you send from a socket you're receiving on (why?)
    pass

  elif ostype == "WindowsCE":
	# No known issues, so just go
	pass
	
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"


# exit all threads
def harshexit(val):

  # The problem is that there can be multiple calls to harshexit before we
  # stop.   For example, a signal (like we may send to kill) may trigger a 
  # call.   As a result, we block all other status writers the first time this
  # is called, but don't later on...
  if not statusexiting[0]:

    # do this once (now)
    statusexiting[0] = True

    # prevent concurrent writes to status info (acquire the lock to stop others,
    # but do not block...
    statuslock.acquire()
  
    # we are stopped by the stop file watcher, not terminated through another 
    # mechanism
    if val == 4:
      # we were stopped by another thread.   Let's exit
      pass
    elif val == 44:
      statusstorage.write_status("Stopped")

    else:
      # generic error, normal exit, or exitall in the user code...
      statusstorage.write_status("Terminated")

    # We intentionally do not release the lock.   We don't want anyone else 
    # writing over our status information (we're killing them).
    

  if ostype == 'Linux':
    # The Nokia N800 refuses to exit on os._exit() by a thread.   I'm going to
    # signal our pid with SIGTERM (or SIGKILL if needed)
    linux_killme()
#    os._exit(val)
  elif ostype == 'Darwin':
    os._exit(val)
  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # stderr is not automatically flushed in Windows...
    sys.stderr.flush()
    os._exit(val)
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"
  


def monitor_cpu_disk_and_mem(cpuallowed, diskallowed, memallowed):
  if ostype == 'Linux' or ostype == 'Darwin':  
    # Startup a CPU monitoring thread/process
    do_forked_cpu_monitor(repy_constants.CPU_POLLING_FREQ_LINUX, cpuallowed)
    
    # Setup a disk and memory thread to enforce the quota
    LinuxResourceNannyThread(repy_constants.RESOURCE_POLLING_FREQ_LINUX, diskallowed, memallowed).start()
    
  elif ostype == 'Windows' or ostype == 'WindowsCE':
    if (ostype == 'WindowsCE'):
      frequency = repy_constants.RESOURCE_POLLING_FREQ_WINCE
      frequencyCPU = repy_constants.CPU_POLLING_FREQ_WINCE
    else:
      frequency = repy_constants.RESOURCE_POLLING_FREQ_WIN
      frequencyCPU = repy_constants.CPU_POLLING_FREQ_WIN
      
    # now we set up a cpu and memory / disk thread nanny...
    # Use an external CPU monitor for WinCE
    if ostype == 'WindowsCE':
      nannypath = "\"" + repy_constants.PATH_SEATTLE_INSTALL + 'win_cpu_nanny.py' + "\""
      cmdline = str(os.getpid())+" "+str(cpuallowed)+" "+str(frequencyCPU)
      windowsAPI.launchPythonScript(nannypath, cmdline)
    else:
      WinCPUNannyThread(frequencyCPU,cpuallowed).start()
    
    # Launch mem./disk resource nanny
    WindowsNannyThread(frequency,diskallowed, memallowed).start()
     
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"


def select_sockets(inlist, timeout = None):

  try:
    # use the built-in select
    (readylist, junk1, exclist) = select.select(inlist, [], inlist, timeout)

  # windows uses socket.error, Mac uses Exception
  except (socket.error, select.error, ValueError), e: 

    # If I'm unsure what this is about, don't handle it here...
    if not isinstance(e, ValueError):
      # socket and select errors of 9 mean it's a closed file descriptor
      # 10038 means it's not a socket
      if e[0] != 9 and e[0] != 10038:
        raise

    # I ignore the timeout because there is obviously an event waiting
    return smarter_select(inlist)


    
  else:  # normal path
    # append any exceptional items to the ready list (likely these are errors
    # that we need to handle)
    for item in exclist:
      if item not in readylist:
        readylist.append(item)

    return readylist



def portablekill(pid):
  if ostype == 'Linux' or ostype == 'Darwin':
    try:
      os.kill(pid, signal.SIGTERM)
    except:
      pass

    try:
      os.kill(pid, signal.SIGKILL)
    except:
      pass

  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # Use new api
    windowsAPI.killProcess(pid)
    
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"


# Data structures and functions for a cross platform CPU limiter

# Intervals to retain for rolling average
ROLLING_PERIOD = 1
rollingCPU = []
rollingIntervals = []

# Debug purposes: Calculate real average
#appstart = time.time()
#rawcpu = 0.0
#totaltime = 0.0

def calculate_cpu_sleep_interval(cpulimit,percentused,elapsedtime):
  """
  <Purpose>
    Calculates proper CPU sleep interval to best achieve target cpulimit.
  
  <Arguments>
    cpulimit:
      The target cpu usage limit
    percentused:
      The percentage of cpu used in the interval between the last sample of the process
    elapsedtime:
      The amount of time elapsed between last sampling the process
  
  <Returns>
    Time period the process should sleep
  """
  global rollingCPU, rollingIntervals
  # Debug: Used to calculate averages
  #global totaltime, rawcpu, appstart

  # Return 0 if elapsedtime is non-positive
  if elapsedtime <= 0:
    return 0
    
  # Update rolling info
  # Use the *moded version of elapsedtime and percentused
  # To account for segmented intervals
  if len(rollingCPU) == ROLLING_PERIOD:
    rollingCPU.pop(0) # Remove oldest CPU data
    rollingIntervals.pop(0) # Remove oldest Elapsed time data
  rollingCPU.append(percentused*elapsedtime) # Add new CPU data
  rollingIntervals.append(elapsedtime) # Add new time data

  # Caclulate Averages
  # Sum up cpu data
  rollingTotalCPU = 0.0
  for i in rollingCPU:
    rollingTotalCPU += i

  # Sum up time data
  rollingTotalTime = 0.0
  for i in rollingIntervals:
    rollingTotalTime += i

  rollingAvg = rollingTotalCPU/rollingTotalTime

  # Calculate Stoptime
  #  Mathematically Derived from:
  #  (PercentUsed * TotalTime) / ( TotalTime + StopTime) = CPULimit
  stoptime = max(((rollingAvg * rollingTotalTime) / cpulimit) - rollingTotalTime , 0)

  # Print debug info
  #rawcpu += percentused*elapsedtime
  #totaltime = time.time() - appstart
  #print totaltime , "," , (rawcpu/totaltime) , "," ,elapsedtime , "," ,percentused
  #print percentused, elapsedtime
  #print "Stopping: ", stoptime

  # Return amount of time to sleep for
  return stoptime

# Elapsed time
elapsedtime = 0

# Store the uptime of the system when we first get loaded
starttime = 0
last_uptime = 0

# Save the number of times windows uptime overflowed
win_overflows = 0

# Timestamp from our starting point
last_timestamp = time.time()

# This is our uptime granularity
granularity = 1

# This ensures only one thread calling getruntime at any given time
runtimelock = threading.Lock()

def getruntime():
  """
   <Purpose>
      Return the amount of time the program has been running.   This is in
      wall clock time.   This function is not guaranteed to always return
      increasing values due to NTP, etc.

   <Arguments>
      None

   <Exceptions>
      None.

   <Side Effects>
      None

   <Remarks>
      By default this will have the same granularity as the system clock. However, if time 
      goes backward due to NTP or other issues, getruntime falls back to system uptime.
      This has much lower granularity, and varies by each system.

   <Returns>
      The elapsed time as float
  """
  global starttime, last_uptime, last_timestamp, win_overflows, elapsedtime, granularity, runtimelock
  
  # Get the lock
  runtimelock.acquire()
  
  # Check if Linux or BSD/Mac
  if ostype in ["Linux", "Darwin"]:
    uptime = getuptime()

    # Check if time is going backward
    if uptime < last_uptime:
      # If the difference is less than 1 second, that is okay, since
      # The boot time is only precise to 1 second
      if (last_uptime - uptime) > 1:
        raise EnvironmentError, "Uptime is going backwards!"
      else:
        # Use the last uptime
        uptime = last_uptime
        
        # No change in uptime
        diff_uptime = 0
    else:  
      # Current uptime, minus the last uptime
      diff_uptime = uptime - last_uptime
      
      # Update last uptime
      last_uptime = uptime

  # Check for windows  
  elif ostype in ["Windows", "WindowsCE"]:   
    #Import the globals
    global win_overflows

    # Uptime is the number of ticks, plus the added limit of unsigned int each time
    # the uptime went backwards
    # Divide by 1000 since it is given in milliseconds
    uptime = (windowsAPI._getTickCount() + win_overflows*windowsAPI.ULONG_MAX) / 1000.0
    
    # Check if uptime is going backward, correct for this
    if uptime < last_uptime:
      uptime += windowsAPI.ULONG_MAX
      win_overflows += 1
    
    # Current uptime, minus the last uptime
    diff_uptime = uptime - last_uptime
      
    # Set the last uptime
    last_uptime = uptime
     

  # Who knows...  
  else:
    raise EnvironmentError, "Unsupported Platform!"
  
  # Current uptime minus start time
  runtime = uptime - starttime
  
  # Get runtime from time.time
  current_time = time.time()
  
  # Current time, minus the last time
  diff_time = current_time - last_timestamp
  
  # Update the last_timestamp
  last_timestamp = current_time
  
  # Is time going backward?
  if diff_time < 0.0:
    # Add in the change in uptime
    elapsedtime += diff_uptime
  
  # Lets check if time.time is too skewed
  else:
    skew = abs(elapsedtime + diff_time - runtime)
    
    # If the skew is too great, use uptime instead of time.time()
    if skew < granularity:
      elapsedtime += diff_time
    else:
      elapsedtime += diff_uptime
  
  # Release the lock
  runtimelock.release()
          
  # Return the new elapsedtime
  return elapsedtime
  
###################     Windows specific functions   #######################


def win_check_memory_use(pid, memlimit):
  # use the process handle to get the memory info
  meminfo = windowsAPI.processMemoryInfo(pid)

  # There are lots of fields in the memory info data.   For example:
  # {'QuotaPagedPoolUsage': 16100L, 'QuotaPeakPagedPoolUsage': 16560L, 
  # 'QuotaNonPagedPoolUsage': 1400L, 'PageFaultCount': 335, 
  # 'PeakWorkingSetSize': 1335296L, 'PeakPagefileUsage': 1486848L, 
  # 'QuotaPeakNonPagedPoolUsage': 1936L, 'PagefileUsage': 1482752L, 
  # 'WorkingSetSize': 45056L}
  #
  # I think the WorkingSetSize is what I want but the Microsoft documentation
  # (http://msdn.microsoft.com/en-us/library/ms684877(VS.85).aspx) is 
  # amazingly useless...

  if meminfo['WorkingSetSize'] > memlimit:
    # We will be killed by the other thread...
    raise Exception, "Memory use '"+str(meminfo['WorkingSetSize'])+"' over limit '"+str(memlimit)+"'"
  

 
# see if the process is over quota and if so raise an exception
def win_check_disk_use(disklimit):
  diskused = misc.compute_disk_use(repy_constants.REPY_CURRENT_DIR)
  
  if diskused > disklimit:
    # We will be killed by the other thread...
    raise Exception, "Disk use '"+str(diskused)+"' over limit '"+str(disklimit)+"'"


class WindowsNannyThread(threading.Thread):
  frequency = None
  memallowed = None
  diskallowed = None
  
  def __init__(self,f,d,m):
    self.frequency = f
    self.diskallowed = d
    self.memallowed = m
    threading.Thread.__init__(self,name="NannyThread")

  def run(self):
    # need my pid to get a process handle...
    mypid = os.getpid()

    # run forever (only exit if an error occurs)
    while True:
      try:
        win_check_disk_use(self.diskallowed)
        win_check_memory_use(mypid, self.memallowed)
	      
        # prevent concurrent status file writes.   
        statuslock.acquire()
        try: 
          # write out status information
          statusstorage.write_status("Started")

        finally:
          # must release before harshexit...
          statuslock.release()

        time.sleep(self.frequency)
        
      except windowsAPI.DeadProcess:
        #  Process may be dead, or die while checking memory use
        #  In any case, there is no reason to continue running, just exit
        harshexit(99)

      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "Nanny died!   Trying to kill everything else"
        harshexit(20)

# Windows specific CPU Nanny Stuff
winlastcpuinfo = [0,0]

# Enfoces CPU limit on Windows and Windows CE
def win_check_cpu_use(cpulim, pid):
  global winlastcpuinfo
  
  # get use information and time...
  now = getruntime()
  usedata = windowsAPI.processTimes(pid)

  # Add kernel and user time together...   It's in units of 100ns so divide
  # by 10,000,000
  usertime = (usedata['KernelTime'] + usedata['UserTime'] ) / 10000000.0
  useinfo = [usertime, now]

  # get the previous time and cpu so we can compute the percentage
  oldusertime = winlastcpuinfo[0]
  oldnow = winlastcpuinfo[1]

  if winlastcpuinfo == [0,0]:
    winlastcpuinfo = useinfo
    # give them a free pass if it's their first time...
    return 0

  # save this data for next time...
  winlastcpuinfo = useinfo

  # Get the elapsed time...
  elapsedtime = now - oldnow

  # This is a problem
  if elapsedtime == 0:
    return -1 # Error condition
    
  # percent used is the amount of change divided by the time...
  percentused = (usertime - oldusertime) / elapsedtime

  # Calculate amount of time to sleep for
  stoptime = calculate_cpu_sleep_interval(cpulim, percentused,elapsedtime)

  # Call new api to suspend/resume process and sleep for specified time
  if windowsAPI.timeoutProcess(pid, stoptime):
    # Return how long we slept so parent knows whether it should sleep
    return stoptime
  else:
    # Process must have been making system call, try again next time
    return -1
    
            
# Dedicated Thread for monitoring CPU, this is run as a part of repy
class WinCPUNannyThread(threading.Thread):
  # Thread variables
  frequency = 0.1 # Sampling frequency
  cpuLimit = 0.1 # CPU % used limit
  pid = 0 # Process pid
  
  def __init__(self,freq,cpulimit):
    self.frequency = freq
    self.cpuLimit = cpulimit
    self.pid = os.getpid()
    threading.Thread.__init__(self,name="CPUNannyThread")
      
  def run(self):
    # Run while the process is running
    while True:
      try:
        # Base amount of sleeping on return value of 
    	  # win_check_cpu_use to prevent under/over sleeping
        slept = win_check_cpu_use(self.cpuLimit, self.pid)
        if slept == -1:
          # Something went wrong, try again
          pass
        elif slept == 0:
          time.sleep(self.frequency)
        elif (slept < self.frequency):
          time.sleep(self.frequency-slept)

      except windowsAPI.DeadProcess:
        #  Process may be dead
        harshexit(97)
        
      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "CPU Nanny died!   Trying to kill everything else"
        harshexit(25)
              
              
#### This seems to be used by Mac as well...

def smarter_select(inlist):
    
  badlist = []
  goodlist = inlist

  # loop until we're either out of sockets to select or we do a clean select
  while goodlist != []:
    try:
      # use the built-in select
      (readylist, junk1, exclist) = select.select(goodlist, [], goodlist, 0.0)
  
    except (socket.error, select.error, ValueError), e:  # windows error path

      # okay, so some socket or sockets are bad.   We need to figure out which 
      # are bad and add them to the badlist...
      newgoodlist = []
      for item in goodlist:
        try:
          # try without blocking.   If it fails, it's bad...
          select.select([item],[],[],0)
          newgoodlist.append(item)
        except (socket.error, select.error, ValueError), e:
          if not isinstance(e, ValueError):
            # socket and select errors of 9 mean it's a closed file descriptor
            # 10038 means it's not a socket
            if e[0] != 9 and e[0] != 10038:
              raise
          badlist.append(item)

      goodlist = newgoodlist

    else:  # normal path
      # append any exceptional items and bad items to the ready list (likely 
      # these are errors that we need to handle)
      for item in exclist:
        if item not in readylist:
          readylist.append(item)

      for item in badlist:
        if item not in readylist:
          readylist.append(item)

      return readylist


  # we're out of options.   Return the badlist...
  return badlist








##############     *nix specific functions (may include Mac)  ###############

# Some import constructs for getuptime
# Constants
CTL_KERN = 1
KERN_BOOTTIME = 21
                
# Get libc
try:
  libc = ctypes.CDLL(ctypes.util.find_library("c"))
except:
  # This may fail on systems where the std C library cannot be found
  # e.g. Windows
  pass

# struct timeval
class timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long),
                ("tv_usec", ctypes.c_long)]
                
# Returns current system uptime of linux and Mac/BSD systems
# This function returns non-decreasing values on Linux, however,
# on Mac/BSD systems due to how the kernel stores the boot-time,
# it is possible to see uptime decrease or increase up to 1 second in the worse conditions
# This is triggered by the system clock being set backwards or forwards
def getuptime():
  # Check if we can use the uptime file
  if os.path.exists("/proc/uptime"):
    # Open the file
    fileHandle = myopen('/proc/uptime', 'r')
    
    # Read in the whole file
    data = fileHandle.read() 
    
    # Split the file by commas, grap the first number and convert to a float
    uptime = float(data.split(" ")[0])
    
    # Close the file
    fileHandle.close()
  else:
    # Get an array with 2 elements, set the syscall parameters
    TwoIntegers = ctypes.c_int * 2
    mib = TwoIntegers(CTL_KERN, KERN_BOOTTIME)
    
    # Get timeval structure, set the size
    boottime = timeval()                
    size = ctypes.c_size_t(ctypes.sizeof(boottime))
    
    # Make the syscall
    libc.sysctl(mib, 2, ctypes.pointer(boottime), ctypes.pointer(size), None, 0)

    # Calculate uptime from current time
    uptime = time.time() - boottime.tv_sec+boottime.tv_usec*1.0e-6
      
  return uptime
  
# Returns the granularity of getuptime
def getgranularity():
  # Chck if /proc/uptime exists
  if os.path.exists("/proc/uptime"):
    # Open the file
    fileHandle = myopen('/proc/uptime', 'r')
    
    # Read in the whole file
    data = fileHandle.read()
    
    # Split the file by commas, grap the first number
    uptime = data.split(" ")[0]
    uptimeDigits = len(uptime.split(".")[1])
    
    # Close the file
    fileHandle.close()
    
    granularity = uptimeDigits
  else:
    # Get an array with 2 elements, set the syscall parameters
    TwoIntegers = ctypes.c_int * 2
    mib = TwoIntegers(CTL_KERN, KERN_BOOTTIME)
    
    # Get timeval structure, set the size
    boottime = timeval()                
    size = ctypes.c_size_t(ctypes.sizeof(boottime))
    
    # Make the syscall
    libc.sysctl(mib, 2, ctypes.pointer(boottime), ctypes.pointer(size), None, 0)
    
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
    
# needed to make the Nokia N800 actually exit on a harshexit...
def linux_killme():
  # ask me nicely
  try:
    os.kill(os.getpid(), signal.SIGTERM)
  except:
    pass

  # then nuke!
  os.kill(os.getpid(), signal.SIGKILL)




# This is a bit of a hack.   The problems are:
# 1) it's really hard to get good cpu information in a portable way unless
#    it's about you.  (ps, etc. are very coarse grained on many systems)
# 2) it's really hard to stop an individual thread
# 
# So it would seem you would need to choose between bad cpu info and poor
# ability to stop threads, unless........
# you have a thread in the program report cpu information to a 
# separate process and use that info to decide if you should stop the program.
# Now you understand why this is such a strange design.

class LinuxCPUTattlerThread(threading.Thread):
  fileobj = None
  frequency = None

  def __init__(self,fobj,f):
    self.fileobj = fobj
    self.frequency = f
    threading.Thread.__init__(self,name="LinuxCPUTattlerThread")

  def run(self):
    # run forever (only exit if an error occurs)
    while True:
      try:
        # tell the monitoring process about my cpu information...
        print >> self.fileobj, repr(list(os.times())+ [getruntime()])
        self.fileobj.flush()

        # prevent concurrent status file writes.   
        statuslock.acquire()
        try:
          # write out status information
          statusstorage.write_status("Started")
        finally:
          # must release before harshexit...
          statuslock.release()


        # wait for some amount of time before telling again
        time.sleep(self.frequency)
      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "LinuxCPUTattler died!   Trying to kill everything else"
        try:
          self.fileobj.close()
        except:
          pass
        harshexit(21)

# Keep track of last stoptime and resume time
resumeTime = 0.0
lastStoptime = 0.0
segmentedInterval = False

# this ensures that the CPU quota is actually enforced on the client
def enforce_cpu_quota(readfobj, cpulimit, frequency, childpid):
  global resumeTime, lastStoptime, segmentedInterval

  elapsedtime, percentused = get_time_and_cpu_percent(readfobj)
  
  # In case of a NTP time shift, we only get thrown off a bit
  # Also, its a sanity check, since negatime elapsed time shouldn't be possible
  #elapsedtime = max(0, min(10 * frequency, elapsedtime))
  
  # They get a free pass (likely their first or last time)
  if elapsedtime == 0.0:
    return

  # Adjust inputs if segment was interrupted
  if segmentedInterval:
    # Reduce elapsed time by the amount spent sleeping
    elapsedtimemod = elapsedtime - lastStoptime 

    # Recalculate percent used based on new elapsed time
    percentusedmod = (percentused * elapsedtime) / elapsedtimemod
  else:
    elapsedtimemod = elapsedtime
    percentusedmod = percentused
  
  #Calculate stop time
  stoptime = calculate_cpu_sleep_interval(cpulimit, percentusedmod, elapsedtimemod)  

  if not stoptime == 0.0:
    # They must be punished by stopping
    os.kill(childpid, signal.SIGSTOP)

    # Sleep until time to resume
    time.sleep(stoptime)

    # And now they can start back up!
    os.kill(childpid, signal.SIGCONT)

    # Save information about wake time and stoptime for future adjustment
    resumeTime = getruntime()
    lastStoptime = stoptime
  else:
    resumeTime = 0.0

  # If stoptime < frequency, then we would over-sample if we don't sleep
  if (stoptime < frequency):
    time.sleep(frequency-stoptime)
  

lastenforcedata = None
WAIT_PERIOD = 0.01 # How long to wait for new data if there is none in the pipe

def get_time_and_cpu_percent(readfobj):
  global lastenforcedata
  global segmentedInterval, resumeTime

  # Default Data Array
  info = [0, 0, 0, 0, 0, 0]
  empty = False # Is the pipe empty?
  num = 0 # How many data sets have we read?
  while not empty or num == 0:
    try:
      # Read in from the Pipe  
      cpudata = readfobj.readline().strip()

      # If the Worker process dies, then the pipe is closed and an EOF is inserted
      # readline will return an empty string on hitting the EOF, so we should detect this and die
      if cpudata == '':
        raise EnvironmentError, "Failed to receive CPU usage data!"

      num += 1
      info = eval(cpudata)

  # This may be thrown because the file descriptor is non-blocking
    except IOError:
       if num == 0: # Sleep a little until data is ready
         time.sleep(WAIT_PERIOD)
       empty = True

  # Give them a free pass the first time
  if not lastenforcedata:
    lastenforcedata = info
    return (0.0, 0.0)

  # The os.times() info is: (cpu, sys, child cpu, child sys, current time)
  # I think it makes the most sense to use the combined cpu/sys time as well
  # as the current time...
  cputime = info[0]
  systime = info[1]
  childcputime = info[2]
  childsystime = info[3]
  clocktime = info[4] 	# processor time (it's in the wrong units...)
  currenttime = info[5]

  # Child time can be non-zero, due to the fact that subprocess uses fork
  # And subprocess is used in the Resource Nanny
  usertime = cputime + systime + childcputime + childsystime

  oldusertime = lastenforcedata[0] + lastenforcedata[1] + lastenforcedata[2] + lastenforcedata[3]
  oldclocktime = lastenforcedata[4]
  oldcurrenttime = lastenforcedata[5]

  # NOTE: Time is going backwards...   Is this possible?   
  # Should do something nicer like ignore quota?
  if currenttime < oldcurrenttime:
    raise Exception, "Elapsed time '"+str(currenttime)+"' less than previous '"+str(oldcurrenttime)+"'"

  # user time is going backwards...   I don't think this is possible
  if usertime < oldusertime:
    raise Exception, "User time '"+str(usertime)+"' at '"+str(currenttime)+"' (uptime) less than user time '"+str(oldusertime)+"' at '"+str(oldcurrenttime)+"' (uptime)"

  # Determine if latest data points contain a segmentation caused by sleeping
  if oldclocktime < resumeTime:
    segmentedInterval = True
  else:
    segmentedInterval = False

  percentused = (usertime - oldusertime) / (clocktime - oldclocktime)
  lastenforcedata = info
  return (currenttime - oldcurrenttime, percentused)

# I use this in the planetlab /proc error case to prevent me from turning off
# memory quotas when /proc is unmounted
badproccount = 0

# see if the process is over quota and if so terminate with extreme prejudice.
def enforce_memory_quota(memorylimit, childpid):
  # PlanetLab proc handling
  global badproccount 

  # issue this command to ps.   This is likely to be non-portable and a source
  # of constant ire...
  memorycmd = 'ps -p '+str(childpid)+' -o rss'
  p = subprocess.Popen(memorycmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
   close_fds=True)
    
  cmddata = p.stdout.read()
  p.stdout.close()
  errdata = p.stderr.read()
  p.stderr.close()
  junkstatus = os.waitpid(p.pid,0)

  #print "C ", cmddata, "E: ", errdata
  # ensure the first line says RSS (i.e. it's normal output
  if 'RSS' == cmddata.split('\n')[0].strip():
    
    # PlanetLab proc handling
    badproccount = 0
  
    # remove the first line
    memorydata = cmddata.split('\n',1)[1]

    # they must have died
    if not memorydata:
      return


    # the answer is in KB, so convert!
    memoryused = int(memorydata)*(2**10)

    if memoryused > memorylimit:
      raise Exception, "Terminated child '"+str(childpid)+"' with memory use '"+str(memoryused)+"' with limit '"+str(memorylimit)+"'"
  
  
  # Perhaps it's similar to my Nokia N800?
  elif 'PID  Uid     VmSize Stat Command' == cmddata.split('\n')[0].strip():

    # PlanetLab proc handling
    badproccount = 0

    # Unfortunately this is a little crazy.  ps prints a full listing of all
    # processes (including threads), however threads show up separately.   
    # furthermore, the memory listed seems to be only the memory for this
    # process.   I have no way of telling:
    # 1) what my threads areif two of my threads that have
    # 4MB of memory

    # walk through the lines and look for the proper pid...
    for line in cmddata.split('\n'):

      if len(line.split()) < 3:
        continue 

      # if the first element of the line is the pid
      if line.split()[0] == str(childpid):
        # the memory data is the third element...
     
        try:
          memorydata = int(line.split()[2])
          break
        except ValueError:
          # They may be a zombie process... (i.e. already exited)
          return

    else:
      # it's not there, did they quit already?
      return
      
    # the answer is in KB, so convert!
    memoryused = int(memorydata)*(2**10)

    if memoryused > memorylimit:
      raise Exception, "Terminated child '"+str(childpid)+"' with memory use '"+str(memoryused)+"' with limit '"+str(memorylimit)+"'"
  
  

  elif cmddata == '' and 'proc' in errdata:
    # PlanetLab /proc error case.   May show up in other environments too...
    # this is the number of consecutive times I've seen this error.
    badproccount = badproccount + 1
    if badproccount > 3:
      raise Exception, "Memory restriction thread had three consecutive /proc errors"
 
  else:
    raise Exception, "Cannot understand '"+memorycmd+"' output: '"+cmddata+"'"
    
# Monitors and restricts disk and memory usage
class LinuxResourceNannyThread(threading.Thread):
  frequency = None
  disklimit = None
  memlimit = None
  pid = None

  def __init__(self, frequency, disk, mem):
    self.frequency = frequency
    self.disklimit = disk
    self.memlimit = mem
    self.pid = os.getpid()
    threading.Thread.__init__(self,name="LinuxResourceNannyThread")

  def run(self):
    # Run forver, monitoring Memory and Disk usage
    while True:
      try:
        # let's check the process and make sure it's not over quota.  
        diskused = misc.compute_disk_use(".")

        # Raise exception if we are over limit
        if diskused > self.disklimit:
          raise Exception, "Disk use '"+str(diskused)+"' over limit '"+str(self.disklimit)+"'"

        # let's check the process and make sure it's not over quota.
        enforce_memory_quota(self.memlimit, self.pid)
        
        # Sleep for a while
        time.sleep(self.frequency)
      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "Resource Nanny died! Trying to exit repy!"
        harshexit(28)
        
        
# Creates a thread to pass CPU info to a process which
# Suspends and resumes the process to maintain CPU throttling
def do_forked_cpu_monitor(frequency, cpulimit):
  # get a pipe for communication
  readpipefd,writepipefd = os.pipe()

  # I'll fork a copy of myself
  childpid = os.fork()

  if childpid == 0:
    # This is the child (we'll let them continue execution and monitor them).
    os.close(readpipefd)
    mywritepipe = os.fdopen(writepipefd,"w")

    # set up a thread to give us CPU info every frequency seconds (roughly)
    LinuxCPUTattlerThread(mywritepipe, frequency).start()
    return

  
  # close the write pipe
  os.close(writepipefd)

  # Needed to setup non-blocking IO operations
  import fcntl

  # Get the flags on the readpipe file descriptor
  flags = fcntl.fcntl(readpipefd, fcntl.F_GETFL, 0)
  # Append non blocking and change the file descriptior
  flags = flags | os.O_NONBLOCK
  fcntl.fcntl (readpipefd, fcntl.F_SETFL, flags)

  myreadpipe = os.fdopen(readpipefd,"r")

  try:	
    #start = time.time() # Used to Determine Overhead
    # wait for them to finish and then exit
    while True:
      # Determine Overhead
      #info = os.times()
      #cpu = info[0] + info[1]
      #print frequency, cpu, time.time()-start, (cpu/(time.time()-start))
	  
      (pid, status) = os.waitpid(childpid,os.WNOHANG)

      # on FreeBSD, the status is non zero when no one waits.  This is 
      # different than the  Linux / Mac semantics
      #if pid == 0 and status == 0:
      if pid == 0:

        try:
          # let's check the process and make sure it's not over quota.  
          enforce_cpu_quota(myreadpipe, cpulimit, frequency, childpid)
        except EnvironmentError:
          # This means that the CPU info pipe is broken, lets figure out why
          # If the process is dead, exit silently
          if os.WIFEXITED(status) or os.WIFSIGNALED(status):
            sys.exit(0)
          # Otherwise, terminate forcefully
          else:
            os.kill(childpid, signal.SIGKILL)
            harshexit(98)
        
        # there is no need to sleep here because we block in enforce_cpu_quota
        # waiting for the child to give us accounting information

        continue

      if childpid != pid:
        raise Exception, "Internal Error: childpid is not pid given by waitpid!"

      # NOTE: there may be weirdness here...
      # after testing, Linux doesn't seem to return from my os.wait if the 
      # process is stopped instead of killed
      #if os.WIFCONTINUED(status) or os.WIFSTOPPED(status):
      #  print "Cont!!!"
      #  continue

      # This is the process exiting
      if os.WIFEXITED(status) or os.WIFSIGNALED(status):
        sys.exit(0)

  except SystemExit:
    raise
  except:
    # try to reveal why we're quitting
    try:
      print >> sys.stderr, "Monitor death!   Impolitely killing child"
      sys.stderr.flush()
    except:
      pass

    # try to kill the child
    try:
      os.kill(childpid, signal.SIGKILL)
    except:
      pass
      
    # re-raise the exception and let the python error handler print it
    raise


###########     functions that help me figure out the os type    ###########

def init_ostype():
  global ostype
  global osrealtype

  # Detect whether or not it is Windows CE/Mobile
  if os.name == 'ce':
    ostype = 'WindowsCE'
    return

  # figure out what sort of witch we are...
  osrealtype = platform.system()

  if osrealtype == 'Linux' or osrealtype == 'Windows' or osrealtype == 'Darwin':
    ostype = osrealtype
    return

  # workaround for a Vista bug...
  if osrealtype == 'Microsoft':
    ostype = 'Windows'
    return

  if osrealtype == 'FreeBSD':
    ostype = 'Linux'
    return

  if osrealtype.startswith('CYGWIN'):
    # I do this because ps doesn't do memory info...   They'll need to add
    # pywin to their copy of cygwin...   I wonder if I should detect its 
    # abscence and tell them (but continue)?
    ostype = 'Windows'
    return

  ostype = 'Unknown'

# Calculates the system granularity
def calculate_granularity():
  global granularity

  if ostype in ["Windows", "WindowsCE"]:
    # The Granularity of getTickCount is 1 millisecond
    granularity = pow(10,-3)
    
  elif ostype == "Linux":
    # We don't know if the granularity is correct yet
    correctGranularity = False
    
    # How many times have we tested
    tests = 0
    
    # Loop while the granularity is incorrect, up to 10 times
    while not correctGranularity and tests <= 10:
      current_granularity = getgranularity()
      uptime_pre = getuptime()
      time.sleep(current_granularity / 10)
      uptime_post = getuptime()
    
      diff = uptime_post - uptime_pre
    
      correctGranularity = int(diff / current_granularity) == (diff / current_granularity)
      tests += 1
    
    granularity = current_granularity
    
  elif ostype == "Darwin":
    granularity = getgranularity()
    
    
# Call init_ostype!!!
init_ostype()

# Set granularity
calculate_granularity()  

# Set the starttime to the initial uptime
starttime = getruntime()
last_uptime = starttime

# Reset elapsed time 
elapsedtime = 0
