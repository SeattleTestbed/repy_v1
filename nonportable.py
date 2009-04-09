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

# used to get information about the system we're running on
import platform

# needed for signal numbers
import signal

import traceback

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

# This prevents writes to the nanny's status information after we want to stop
statuslock = statusstorage.statuslock

# This will fail on non-windows systems
try:
  import windows_api as windowsAPI
except:
  windowsAPI = None
  pass

# Armon: This is a place holder for the module that will be imported later
osAPI = None

# Armon: See additional imports at the bottom of the file


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
    
    # Special Termination signal to notify the NM of excessive threads
    elif val == 56:
      statusstorage.write_status("ThreadErr")
      
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
    portablekill(os.getpid())
#    os._exit(val)
  elif ostype == 'Darwin':
    os._exit(val)
  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # stderr is not automatically flushed in Windows...
    sys.stderr.flush()
    os._exit(val)
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"
  


def monitor_cpu_disk_and_mem():
  if ostype == 'Linux' or ostype == 'Darwin':  
    # Startup a CPU monitoring thread/process
    do_forked_resource_monitor()
    
  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # Now we set up a cpu nanny...
    # Use an external CPU monitor for WinCE
    if ostype == 'WindowsCE':
      nannypath = "\"" + repy_constants.PATH_SEATTLE_INSTALL + 'win_cpu_nanny.py' + "\""
      cmdline = str(os.getpid())+" "+str(nanny.resource_limit("cpu"))+" "+str(repy_constants.CPU_POLLING_FREQ_WINCE)
      windowsAPI.launchPythonScript(nannypath, cmdline)
    else:
      WinCPUNannyThread().start()
    
    # Launch mem./disk resource nanny
    WindowsNannyThread().start()
     
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



# Elapsed time
elapsedtime = 0

# Store the uptime of the system when we first get loaded
starttime = 0
last_uptime = 0

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
  global starttime, last_uptime, last_timestamp, elapsedtime, granularity, runtimelock
  
  # Get the lock
  runtimelock.acquire()
  
  # Check if Linux or BSD/Mac
  if ostype in ["Linux", "Darwin"]:
    uptime = osAPI.getSystemUptime()

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
    # Release the lock
    runtimelock.release()
    
    # Time.clock returns elapsedtime since the first call to it, so this works for us
    return time.clock()
     
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

class WindowsNannyThread(threading.Thread):

  def __init__(self):
    threading.Thread.__init__(self,name="NannyThread")

  def run(self):
    # Calculate how often disk should be checked
    if ostype == "WindowsCE":
      diskInterval = int(repy_constants.RESOURCE_POLLING_FREQ_WINCE / repy_constants.CPU_POLLING_FREQ_WINCE)
    else:
      diskInterval = int(repy_constants.RESOURCE_POLLING_FREQ_WIN / repy_constants.CPU_POLLING_FREQ_WIN)
    currentInterval = 0 # What cycle are we on  
    
    # Elevate our priority, above normal is higher than the usercode, and is enough for disk/mem
    windowsAPI.setCurrentThreadPriority(windowsAPI.THREAD_PRIORITY_ABOVE_NORMAL)
    
    # need my pid to get a process handle...
    mypid = os.getpid()

    # run forever (only exit if an error occurs)
    while True:
      try:
        # Check memory use, get the WorkingSetSize or RSS
        memused = windowsAPI.processMemoryInfo(mypid)['WorkingSetSize']
        
        if memused > nanny.resource_limit("memory"):
          # We will be killed by the other thread...
          raise Exception, "Memory use '"+str(memused)+"' over limit '"+str(nanny.resource_limit("memory"))+"'"
        
        # Increment the interval we are on
        currentInterval += 1

        # Check if we should check the disk
        if (currentInterval % diskInterval) == 0:
          # Check diskused
          diskused = misc.compute_disk_use(repy_constants.REPY_CURRENT_DIR)
          if diskused > nanny.resource_limit("diskused"):
            raise Exception, "Disk use '"+str(diskused)+"' over limit '"+str(nanny.resource_limit("diskused"))+"'"
        
        if ostype == 'WindowsCE':
          time.sleep(repy_constants.CPU_POLLING_FREQ_WINCE)
        else:
          time.sleep(repy_constants.CPU_POLLING_FREQ_WIN)
        
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
  stoptime = nanny.calculate_cpu_sleep_interval(cpulim, percentused,elapsedtime)

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
  pid = 0 # Process pid
  
  def __init__(self):
    self.pid = os.getpid()
    threading.Thread.__init__(self,name="CPUNannyThread")    
      
  def run(self):
    # Elevate our priority, set us to the highest so that we can more effectively throttle
    success = windowsAPI.setCurrentThreadPriority(windowsAPI.THREAD_PRIORITY_HIGHEST)
    
    # If we failed to get HIGHEST priority, try above normal, else we're still at default
    if not success:
      windowsAPI.setCurrentThreadPriority(windowsAPI.THREAD_PRIORITY_ABOVE_NORMAL)
    
    # Run while the process is running
    while True:
      try:
        # Get the frequency
        frequency = repy_constants.CPU_POLLING_FREQ_WIN
        
        # Base amount of sleeping on return value of 
    	  # win_check_cpu_use to prevent under/over sleeping
        slept = win_check_cpu_use(nanny.resource_limit("cpu"), self.pid)
        
        if slept == -1:
          # Something went wrong, try again
          pass
        elif (slept < frequency):
          time.sleep(frequency-slept)

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
                
# Use a special class of exception for when
# resource limits are exceeded
class ResourceException(Exception):
  pass

        
# Forks Repy. The child will continue execution, and the parent
# will become a resource monitor
def do_forked_resource_monitor():
  # I'll fork a copy of myself
  childpid = os.fork()

  if childpid == 0:
    return
  
  # Small internal error handler function
  def _internal_error(message):
    try:
      print >> sys.stderr, message
      sys.stderr.flush()
    except:
      pass

    # Kill repy
    portablekill(childpid)

    try:
      # Write out status information, repy was Stopped
      statusstorage.write_status("Terminated")  
    except:
      pass
  
  try:
    # Some OS's require that you wait on the PID at least once
    # before they do any accounting
    (pid, status) = os.waitpid(childpid,os.WNOHANG)
    
    # Launch the resource monitor, if it fails determine why and restart if necessary
    resource_monitor(childpid)
    
  except ResourceException, exp:
    # Repy exceeded its resource limit, kill it
    _internal_error(str(exp)+" Impolitely killing child!")
    harshexit(98)
    
  except Exception, exp:
    # There is some general error...
    try:
      (pid, status) = os.waitpid(childpid,os.WNOHANG)
    except:
      # This means that the process is dead
      pass
    
    # Check if this is repy exiting
    if os.WIFEXITED(status) or os.WIFSIGNALED(status):
      sys.exit(0)
    
    else:
      _internal_error(str(exp)+" Monitor death! Impolitely killing child!")
      raise
  
def resource_monitor(childpid):
  """
  <Purpose>
    Function runs in a loop forever, checking resource usage and throttling CPU.
    Checks CPU, memory, and disk.
    
  <Arguments>
    childpid:
      The child pid, e.g. the PID of repy
  """
  # Get our pid
  ourpid = os.getpid()
  
  # Calculate how often disk should be checked
  diskInterval = int(repy_constants.RESOURCE_POLLING_FREQ_LINUX / repy_constants.CPU_POLLING_FREQ_LINUX)
  currentInterval = 0 # What cycle are we on  
  
  # Store time of the last interval
  lastTime = getruntime()
  lastCPUTime = 0
  resumeTime = 0 
  
  # Run forever...
  while True:
    ########### Check CPU ###########
    # Get elasped time
    currenttime = getruntime()
    elapsedtime1 = currenttime - lastTime     # Calculate against last run
    elapsedtime2 = currenttime - resumeTime   # Calculate since we last resumed repy
    elapsedtime = min(elapsedtime1, elapsedtime2) # Take the minimum interval
    lastTime = currenttime  # Save the current time
    
    # Safety check, prevent ZeroDivisionError
    if elapsedtime == 0.0:
      continue
    
    # Get the total cpu at this point
    totalCPU =  osAPI.getProcessCPUTime(ourpid)   # Our own usage
    totalCPU += osAPI.getProcessCPUTime(childpid) # Repy's usage
    
    # Calculate percentage of CPU used
    percentused = (totalCPU - lastCPUTime) / elapsedtime
    
    # Do not throttle for the first interval, wrap around
    # Store the totalCPU for the next cycle
    if lastCPUTime == 0:
      lastCPUTime = totalCPU    
      continue
    else:
      lastCPUTime = totalCPU
      
    # Calculate stop time
    stoptime = nanny.calculate_cpu_sleep_interval(nanny.resource_limit("cpu"), percentused, elapsedtime)
    
    # If we are supposed to stop repy, then suspend, sleep and resume
    if stoptime > 0.0:
      # They must be punished by stopping
      os.kill(childpid, signal.SIGSTOP)

      # Sleep until time to resume
      time.sleep(stoptime)

      # And now they can start back up!
      os.kill(childpid, signal.SIGCONT)
      
      # Save the resume time
      resumeTime = getruntime()
      
    
    ########### End Check CPU ###########
    # 
    ########### Check Memory ###########
    
    # Get how much memory repy is using
    memused = osAPI.getProcessRSS()
    
    # Check if it is using too much memory
    if memused > nanny.resource_limit("memory"):
      raise ResourceException, "Memory use '"+str(memused)+"' over limit '"+str(nanny.resource_limit("memory"))+"'."
    
    ########### End Check Memory ###########
    # 
    ########### Check Disk Usage ###########
    # Increment our current cycle
    currentInterval += 1;
    
    # Check if it is time to check the disk usage
    if (currentInterval % diskInterval) == 0:
      # Reset the interval
      currentInterval = 0
       
      # Calculate disk used
      diskused = misc.compute_disk_use(repy_constants.REPY_CURRENT_DIR)

      # Raise exception if we are over limit
      if diskused > nanny.resource_limit("diskused"):
        raise ResourceException, "Disk use '"+str(diskused)+"' over limit '"+str(nanny.resource_limit("diskused"))+"'."
    
    ########### End Check Disk ###########
    
    # Sleep before the next iteration
    time.sleep(repy_constants.CPU_POLLING_FREQ_LINUX)


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
      current_granularity = osAPI.getUptimeGranularity()
      uptime_pre = osAPI.getSystemUptime()
      time.sleep(current_granularity / 10)
      uptime_post = osAPI.getSystemUptime()
    
      diff = uptime_post - uptime_pre
    
      correctGranularity = int(diff / current_granularity) == (diff / current_granularity)
      tests += 1
    
    granularity = current_granularity
    
  elif ostype == "Darwin":
    granularity = osAPI.getUptimeGranularity()
    
    
# Call init_ostype!!!
init_ostype()

# Import the proper system wide API
if osrealtype == "Linux":
  import linux_api as osAPI
elif osrealtype == "Darwin":
  import darwin_api as osAPI
elif osrealtype == "FreeBSD":
  import freebsd_api as osAPI
elif ostype == "Windows" or ostype == "WindowsCE":
  # There is no real reason to do this, since windows is imported separately
  import windows_api as osAPI
else:
  # This is a non-supported OS
  raise UnsupportedSystemException, "The current Operating System is not supported! Fatal Error."
  
# Set granularity
calculate_granularity()  

# For Windows, we need to initialize time.clock()
if ostype in ["Windows", "WindowsCE"]:
  time.clock()

# Initialize getruntime for other platforms 
else:
  # Set the starttime to the initial uptime
  starttime = getruntime()
  last_uptime = starttime

  # Reset elapsed time 
  elapsedtime = 0


# Armon: import tracebackrepy must come after nonportable is initialized
# because it has a chain of dependencies which calls into nonportable
# if it is imported at the top, nanny attempts to make calls into nonportable before the module
# has finished importing its dependencies
# print useful info when exiting...
import tracebackrepy  

# Armon: See above reason. (Prevents circular imports)
# This gives us our restrictions information
import nanny


