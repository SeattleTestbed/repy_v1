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

# needed for signal numbers
import signal

# needed for harshexit
import harshexit


# used to query status, etc.
# This may fail on Windows CE
try:
  import subprocess
  mobile_no_subprocess = False
except ImportError:
  # Set flag to avoid using subprocess
  mobile_no_subprocess = True 

# used for select (duh)
import select

# used for socket.error
import socket

# need for status retrieval
import statusstorage

# Get constants
import repy_constants

# Get access to the status interface so we can start it
import nmstatusinterface

# This gives us our restrictions information
import nanny_resource_limits

# This will fail on non-windows systems
try:
  import windows_api as windows_api
except:
  windows_api = None

# Armon: This is a place holder for the module that will be imported later
os_api = None

# Armon: See additional imports at the bottom of the file

class UnsupportedSystemException(Exception):
  pass



###################     Publicly visible functions   #######################

# check the disk space used by a dir.
def compute_disk_use(dirname):
  # Convert path to absolute
  dirname = os.path.abspath(dirname)
  
  diskused = 0
  
  for filename in os.listdir(dirname):
    try:
      diskused = diskused + os.path.getsize(os.path.join(dirname, filename))
    except IOError:   # They likely deleted the file in the meantime...
      pass
    except OSError:   # They likely deleted the file in the meantime...
      pass

    # charge an extra 4K for each file to prevent lots of little files from 
    # using up the disk.   I'm doing this outside of the except clause in
    # the failure to get the size wasn't related to deletion
    diskused = diskused + 4096
        
  return diskused


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
  

# Armon: Also launches the nmstatusinterface thread.
# This will result in an internal thread on Windows
# and a thread on the external process for *NIX
def monitor_cpu_disk_and_mem():
  if ostype == 'Linux' or ostype == 'Darwin':  
    # Startup a CPU monitoring thread/process
    do_forked_resource_monitor()
    
  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # Now we set up a cpu nanny...
    # Use an external CPU monitor for WinCE
    if ostype == 'WindowsCE':
      nannypath = "\"" + repy_constants.PATH_SEATTLE_INSTALL + 'win_cpu_nanny.py' + "\""
      cmdline = str(os.getpid())+" "+str(nanny_resource_limits.resource_limit("cpu"))+" "+str(repy_constants.CPU_POLLING_FREQ_WINCE)
      windows_api.launch_python_script(nannypath, cmdline)
    else:
      WinCPUNannyThread().start()
    
    # Launch mem./disk resource nanny
    WindowsNannyThread().start()
    
    # Start the nmstatusinterface. Windows means repy isn't run in an external
    # process, so pass None instead of a process id.
    nmstatusinterface.launch(None)
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
    uptime = os_api.get_system_uptime()

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
      disk_interval = int(repy_constants.RESOURCE_POLLING_FREQ_WINCE / repy_constants.CPU_POLLING_FREQ_WINCE)
    else:
      disk_interval = int(repy_constants.RESOURCE_POLLING_FREQ_WIN / repy_constants.CPU_POLLING_FREQ_WIN)
    current_interval = 0 # What cycle are we on  
    
    # Elevate our priority, above normal is higher than the usercode, and is enough for disk/mem
    windows_api.set_current_thread_priority(windows_api.THREAD_PRIORITY_ABOVE_NORMAL)
    
    # need my pid to get a process handle...
    mypid = os.getpid()

    # run forever (only exit if an error occurs)
    while True:
      try:
        # Check memory use, get the WorkingSetSize or RSS
        memused = windows_api.process_memory_info(mypid)['WorkingSetSize']
        
        if memused > nanny_resource_limits.resource_limit("memory"):
          # We will be killed by the other thread...
          raise Exception, "Memory use '"+str(memused)+"' over limit '"+str(nanny_resource_limits.resource_limit("memory"))+"'"
        
        # Increment the interval we are on
        current_interval += 1

        # Check if we should check the disk
        if (current_interval % disk_interval) == 0:
          # Check diskused
          diskused = compute_disk_use(repy_constants.REPY_CURRENT_DIR)
          if diskused > nanny_resource_limits.resource_limit("diskused"):
            raise Exception, "Disk use '"+str(diskused)+"' over limit '"+str(nanny_resource_limits.resource_limit("diskused"))+"'"
        
        if ostype == 'WindowsCE':
          time.sleep(repy_constants.CPU_POLLING_FREQ_WINCE)
        else:
          time.sleep(repy_constants.CPU_POLLING_FREQ_WIN)
        
      except windows_api.DeadProcess:
        #  Process may be dead, or die while checking memory use
        #  In any case, there is no reason to continue running, just exit
        harshexit.harshexit(99)

      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "Nanny died!   Trying to kill everything else"
        harshexit.harshexit(20)


# Windows specific CPU Nanny Stuff
winlastcpuinfo = [0,0]

# Enfoces CPU limit on Windows and Windows CE
def win_check_cpu_use(cpulim, pid):
  global winlastcpuinfo
  
  # get use information and time...
  now = getruntime()
  usedata = windows_api.process_times(pid)

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
  stoptime = nanny_resource_limits.calculate_cpu_sleep_interval(cpulim, percentused,elapsedtime)

  # Call new api to suspend/resume process and sleep for specified time
  if windows_api.timeout_process(pid, stoptime):
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
    success = windows_api.set_current_thread_priority(windows_api.THREAD_PRIORITY_HIGHEST)
    
    # If we failed to get HIGHEST priority, try above normal, else we're still at default
    if not success:
      windows_api.set_current_thread_priority(windows_api.THREAD_PRIORITY_ABOVE_NORMAL)
    
    # Run while the process is running
    while True:
      try:
        # Get the frequency
        frequency = repy_constants.CPU_POLLING_FREQ_WIN
        
        # Base amount of sleeping on return value of 
    	  # win_check_cpu_use to prevent under/over sleeping
        slept = win_check_cpu_use(nanny_resource_limits.resource_limit("cpu"), self.pid)
        
        if slept == -1:
          # Something went wrong, try again
          pass
        elif (slept < frequency):
          time.sleep(frequency-slept)

      except windows_api.DeadProcess:
        #  Process may be dead
        harshexit.harshexit(97)
        
      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "CPU Nanny died!   Trying to kill everything else"
        harshexit.harshexit(25)
              
              
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


# Armon: A simple thread to check for the parent process
# and exit repy if the parent terminates
class parent_process_checker(threading.Thread):
  def __init__(self, readhandle):
    """
    <Purpose>
      Terminates harshly if our parent dies before we do.

    <Arguments>
      readhandle: A file descriptor to the handle of a pipe to our parent.
    """
    # Name our self
    threading.Thread.__init__(self, name="ParentProcessChecker")

    # Store the handle
    self.readhandle = readhandle

  def run(self):
    # Attempt to read 8 bytes from the pipe, this should block until we end execution
    try:
      mesg = os.read(self.readhandle,8)
    except:
      # It is possible we got an interrupted system call (on FreeBSD) when the parent is killed
      mesg = ""

    # Write out status information, our parent would do this, but its dead.
    statusstorage.write_status("Terminated")  
    
    # Check the message. If it is the empty string the pipe was closed, 
    # if there is any data, this is unexpected and is also an error.
    if mesg == "":
      print >> sys.stderr, "Monitor process died! Terminating!"
      harshexit.harshexit(70)
    else:
      print >> sys.stderr, "Unexpectedly received data! Terminating!"
      harshexit.harshexit(71)



# For *NIX systems, there is an external process, and the 
# pid for the actual repy process is stored here
repy_process_id = None

# Forks Repy. The child will continue execution, and the parent
# will become a resource monitor
def do_forked_resource_monitor():
  global repy_process_id

  # Get a pipe
  (readhandle, writehandle) = os.pipe()

  # I'll fork a copy of myself
  childpid = os.fork()

  if childpid == 0:
    # We are the child, close the write end of the pipe
    os.close(writehandle)

    # Start a thread to check on the survival of the parent
    parent_process_checker(readhandle).start()

    return
  else:
    # We are the parent, close the read end
    os.close(readhandle)

  # Store the childpid
  repy_process_id = childpid

  # Start the nmstatusinterface
  nmstatusinterface.launch(repy_process_id)
  
  # Small internal error handler function
  def _internal_error(message):
    try:
      print >> sys.stderr, message
      sys.stderr.flush()
    except:
      pass
      
    # Stop the nmstatusinterface, we don't want any more status updates
    nmstatusinterface.stop()  

    # Kill repy
    harshexit.portablekill(childpid)

    try:
      # Write out status information, repy was Stopped
      statusstorage.write_status("Terminated")  
    except:
      pass
  
  try:
    # Some OS's require that you wait on the pid at least once
    # before they do any accounting
    (pid, status) = os.waitpid(childpid,os.WNOHANG)
    
    # Launch the resource monitor, if it fails determine why and restart if necessary
    resource_monitor(childpid)
    
  except ResourceException, exp:
    # Repy exceeded its resource limit, kill it
    _internal_error(str(exp)+" Impolitely killing child!")
    harshexit.harshexit(98)
    
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
      The child pid, e.g. the pid of repy
  """
  # Get our pid
  ourpid = os.getpid()
  
  # Calculate how often disk should be checked
  disk_interval = int(repy_constants.RESOURCE_POLLING_FREQ_LINUX / repy_constants.CPU_POLLING_FREQ_LINUX)
  current_interval = 0 # What cycle are we on  
  
  # Store time of the last interval
  last_time = getruntime()
  last_CPU_time = 0
  resume_time = 0 
  
  # Run forever...
  while True:
    ########### Check CPU ###########
    # Get elasped time
    currenttime = getruntime()
    elapsedtime1 = currenttime - last_time     # Calculate against last run
    elapsedtime2 = currenttime - resume_time   # Calculate since we last resumed repy
    elapsedtime = min(elapsedtime1, elapsedtime2) # Take the minimum interval
    last_time = currenttime  # Save the current time
    
    # Safety check, prevent ZeroDivisionError
    if elapsedtime == 0.0:
      continue
    
    # Get the total cpu at this point
    totalCPU =  os_api.get_process_cpu_time(ourpid)   # Our own usage
    totalCPU += os_api.get_process_cpu_time(childpid) # Repy's usage
    
    # Calculate percentage of CPU used
    percentused = (totalCPU - last_CPU_time) / elapsedtime
    
    # Do not throttle for the first interval, wrap around
    # Store the totalCPU for the next cycle
    if last_CPU_time == 0:
      last_CPU_time = totalCPU    
      continue
    else:
      last_CPU_time = totalCPU
      
    # Calculate stop time
    stoptime = nanny_resource_limits.calculate_cpu_sleep_interval(nanny_resource_limits.resource_limit("cpu"), percentused, elapsedtime)
    
    # If we are supposed to stop repy, then suspend, sleep and resume
    if stoptime > 0.0:
      # They must be punished by stopping
      os.kill(childpid, signal.SIGSTOP)

      # Sleep until time to resume
      time.sleep(stoptime)

      # And now they can start back up!
      os.kill(childpid, signal.SIGCONT)
      
      # Save the resume time
      resume_time = getruntime()
      
    
    ########### End Check CPU ###########
    # 
    ########### Check Memory ###########
    
    # Get how much memory repy is using
    memused = os_api.get_process_rss()
    
    # Check if it is using too much memory
    if memused > nanny_resource_limits.resource_limit("memory"):
      raise ResourceException, "Memory use '"+str(memused)+"' over limit '"+str(nanny_resource_limits.resource_limit("memory"))+"'."
    
    ########### End Check Memory ###########
    # 
    ########### Check Disk Usage ###########
    # Increment our current cycle
    current_interval += 1;
    
    # Check if it is time to check the disk usage
    if (current_interval % disk_interval) == 0:
      # Reset the interval
      current_interval = 0
       
      # Calculate disk used
      diskused = compute_disk_use(repy_constants.REPY_CURRENT_DIR)

      # Raise exception if we are over limit
      if diskused > nanny_resource_limits.resource_limit("diskused"):
        raise ResourceException, "Disk use '"+str(diskused)+"' over limit '"+str(nanny_resource_limits.resource_limit("diskused"))+"'."
    
    ########### End Check Disk ###########
    
    # Sleep before the next iteration
    time.sleep(repy_constants.CPU_POLLING_FREQ_LINUX)


###########     functions that help me figure out the os type    ###########

# Calculates the system granularity
def calculate_granularity():
  global granularity

  if ostype in ["Windows", "WindowsCE"]:
    # The Granularity of getTickCount is 1 millisecond
    granularity = pow(10,-3)
    
  elif ostype == "Linux":
    # We don't know if the granularity is correct yet
    correct_granularity = False
    
    # How many times have we tested
    tests = 0
    
    # Loop while the granularity is incorrect, up to 10 times
    while not correct_granularity and tests <= 10:
      current_granularity = os_api.get_uptime_granularity()
      uptime_pre = os_api.get_system_uptime()
      time.sleep(current_granularity / 10)
      uptime_post = os_api.get_system_uptime()
    
      diff = uptime_post - uptime_pre
    
      correct_granularity = int(diff / current_granularity) == (diff / current_granularity)
      tests += 1
    
    granularity = current_granularity
    
  elif ostype == "Darwin":
    granularity = os_api.get_uptime_granularity()
    


# Call init_ostype!!!
harshexit.init_ostype()

ostype = harshexit.ostype
osrealtype = harshexit.osrealtype

# Import the proper system wide API
if osrealtype == "Linux":
  import linux_api as os_api
elif osrealtype == "Darwin":
  import darwin_api as os_api
elif osrealtype == "FreeBSD":
  import freebsd_api as os_api
elif ostype == "Windows" or ostype == "WindowsCE":
  # There is no real reason to do this, since windows is imported separately
  import windows_api as os_api
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

# Conrad: initialize nanny (Prevents circular imports)
# Note: nanny_resource_limits can be initialized at any time after getruntime()
# is defined, this just seems the most appropriate place to put the call.
nanny_resource_limits.init(getruntime)
