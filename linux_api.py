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
import subprocess

import nix_common_api as nixAPI # Import the Common API

# Manually import the common functions we want
existsListeningNetworkSocket = nixAPI.existsListeningNetworkSocket

# Get the standard library
libc = ctypes.CDLL(ctypes.util.find_library("c"))

# Functions
myopen = open # This is an annoying restriction of repy

# Globals
lastStatData = None   # Store the last array of data from _getProcInfoByPID

# Constants
JIFFIES_PER_SECOND = 100.0
PAGE_SIZE = os.sysconf('SC_PAGESIZE')

# Maps each field in /proc/{PID}/stat to an index when split by spaces
FIELDS = {
"pid":0,
"state":1,
"ppid":2,
"pgrp":3,
"session":4,
"tty_nr":5,
"tpgid":6,
"flags":7,
"minflt":8,
"cminflt":9,
"majflt":10,
"cmajflt":11,
"utime":12,
"stime":13,
"cutime":14,
"cstime":15,
"priority":16,
"nice":17,
"num_threads":18,
"itrealvalue":19,
"starttime":20,
"vsize":21,
"rss":22,
"rlim":23,
"startcode":24,
"endcode":25,
"startstack":26,
"kstkesp":27,
"kstkeoip":28,
"signal":29,
"blocked":30,
"sigignore":31,
"sigcatch":32,
"wchan":33,
"nswap":34,
"cnswap":35,
"exit_signal":36,
"processor":37,
"rt_priority":38,
"policy":39,
"delayacct_blkio_ticks":40
}


def _getProcInfoByPID(PID):
  """
  <Purpose>
    Reads in the data from a process stat file, and stores it
  
  <Arguments>
    PID: The process identifier for which data should be fetched.  
  """
  global lastStatData

  # Get the file in proc
  fileo = open("/proc/"+str(PID)+"/stat","r")

  # Read in all the data
  data = fileo.read()

  # Close the file object
  fileo.close()

  # Strip the newline
  data = data.strip("\n")

  # Remove the substring that says "(python)", since it changes the field alignment
  startIndex = data.find("(")
  if startIndex != -1:
    endIndex = data.find(")",startIndex)
    data = data[:startIndex-1] + data[endIndex+1:]

  # Break the data into an array by spaces
  lastStatData = data.split(" ")
  
  # Check the state, raise an exception if the process is a zombie
  if "Z" in lastStatData[FIELDS["state"]]:
    raise Exception, "Queried Process is a zombie (dead)!"
  
  
def getProcessCPUTime(PID):
  """
  <Purpose>
    Returns the total CPU time used by a process.
    
  <Arguments>
    PID: The process identifier for the process to query.
  
  <Returns>
    The total cpu time.
  """
  global lastStatData
  
  # Update our data
  _getProcInfoByPID(PID)
  
  # Get the raw usertime and system time
  totalTimeRaw = int(lastStatData[FIELDS["utime"]])+int(lastStatData[FIELDS["stime"]])
  
  # Adjust by the number of jiffies per second
  totalTime = totalTimeRaw / JIFFIES_PER_SECOND
  
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

  <Returns>
    The RSS of the process in bytes.
  """
  global lastStatData

  # Check if an update is being forced
  if forceUpdate and PID != None:
    # Update the info
    _getProcInfoByPID(PID)

  # Fetch the RSS, convert to an integer
  RSS_Pages = int(lastStatData[FIELDS["rss"]])
  RSS_Bytes = RSS_Pages * PAGE_SIZE

  # Return the info
  return RSS_Bytes

def getSystemUptime():
  """
  <Purpose>
    Returns the system uptime.

  <Exception>
    Raises Exception if /proc/uptime is unavailable
    
  <Returns>
    The system uptime.  
  """
  if os.path.exists("/proc/uptime"):
    # Open the file
    fileHandle = myopen('/proc/uptime', 'r')
    
    # Read in the whole file
    data = fileHandle.read() 
    
    # Split the file by commas, grap the first number and convert to a float
    uptime = float(data.split(" ")[0])
    
    # Close the file
    fileHandle.close()
    
    return uptime
  else:
    raise Exception, "Could not find /proc/uptime!"
  
def getUptimeGranularity():
  """
  <Purpose>
    Determines the granularity of the getSystemUptime call.
  
  <Exception>
    Raises Exception if /proc/uptime is unavailable
        
  <Returns>
    A numerical representation of the minimum granularity.
    E.g. 2 digits of granularity would return 0.01
  """
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
    
    # Convert granularity to a number
    return pow(10, 0-granularity)
  else:
    raise Exception, "Could not find /proc/uptime!"  


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


