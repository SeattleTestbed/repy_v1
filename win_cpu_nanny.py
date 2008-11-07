""" 
Author: Justin Cappos

Start Date: July 4th, 2008

Description:
Is the nanny for cpu on Windows.
"""

import os
import time
import sys
import tracebackrepy

try:
  import windows_api
  windowsAPI = windows_api
except:
  try:
    import windows_ce_api
    windowsAPI = windows_ce_api
  except:
    windowsAPI = None
    pass
  pass

winlastcpuinfo = [0,0]
firststart = None
firstcpu = None

# Intervals to retain for rolling average
ROLLING_PERIOD = 1
rollingCPU = []
rollingIntervals = []

# Keep track of last stoptime and resume time
resumeTime = 0.0
lastStoptime = 0.0
segmentedInterval = False

# Debug purposes: Calculate real average
#rawcpu = 0.0
#totaltime = 0.0

def win_check_cpu_use(cpulimit,pid):
  global rollingCPU, rollingIntervals
  global resumeTime, lastStoptime, segmentedInterval
  # Debug: Used to calculate averages
  #global totaltime, rawcpu
  global firststart
  global firstcpu
  global winlastcpuinfo

  # get use information and time...
  now = time.time()
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
    firststart = now
    firstcpu = usertime
    # give them a free pass if it's their first time...
    return 0

  # save this data for next time...
  winlastcpuinfo = useinfo

  # Get the elapsed time...
  elapsedtime = now - oldnow

  # percent used is the amount of change divided by the time...
  percentused = (usertime - oldusertime) / elapsedtime
 
  # Adjust inputs if segment was interrupted
  if segmentedInterval:
    # Reduce elapsed time by the amount spent sleeping
    elapsedtimemod = elapsedtime - lastStoptime 

    # Recalculate percent used based on new elapsed time
    percentusedmod = (percentused * elapsedtime) / elapsedtimemod
  else:
    elapsedtimemod = elapsedtime
    percentusedmod = percentused

  # Update rolling info
  # Use the *moded version of elapsedtime and percentused
  # To account for segmented intervals
  if len(rollingCPU) == ROLLING_PERIOD:
    rollingCPU.pop(0) # Remove oldest CPU data
    rollingIntervals.pop(0) # Remove oldest Elapsed time data
  rollingCPU.append(percentusedmod*elapsedtimemod) # Add new CPU data
  rollingIntervals.append(elapsedtimemod) # Add new time data

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
  #totaltime += elapsedtime
  #print totaltime , "," ,rollingAvg, ",", (rawcpu/totaltime) , "," ,percentused
  #print "Stopping: ", stoptime


  # Call new api to suspend/resume process and sleep for specified time
  if windowsAPI.timeoutProcess(pid, stoptime):
    # Save information about wake time and stoptime for future adjustment
    resumeTime = time.time()
    lastStoptime = stoptime

    # Return how long we slept so parent knows whether it should sleep
    return stoptime
  else:
    # Process must have been making system call, try again next time
    return -1	

def main():

  if len(sys.argv) != 4:
    print "Error, didn't get the right number of args:",sys.argv
    sys.exit(1)

  ppid = int(sys.argv[1])
  limit = float(sys.argv[2])
  freq = float(sys.argv[3])

  # run forever, checking the process' memory use and stopping when appropriate
  try:
    while True:
	  # Base amount of sleeping on return value of 
	  # win_check_cpu_use to prevent under/over sleeping
      slept = win_check_cpu_use(limit, ppid)

      if slept == -1:
        # Something went wrong, try again
        pass
      elif slept == 0:
        time.sleep(freq)
      elif (slept < freq):
        time.sleep(freq-slept)
    
      # see if the process exited...
      status = windowsAPI.processExitCode(ppid)
      # Amazing! They rely on the programmer to not return 259 to know when 
      # something actually exited.   Luckily, I do control the return codes...
      if status != 259:
        sys.exit(0)

  except SystemExit:
    pass

  except windows_api.DeadProcess:
    # This can be caused when getting process times for a dead thread or
    # Trying to timeout a dead thread, either way, we just exit
    sys.exit(0)

  except:
    tracebackrepy.handle_exception()
    print >> sys.stderr, "Win nanny died!   Trying to kill everything else"
    
    # kill the program we're monitoring
    # Use newer api to kill process
    windowsAPI.killProcess(ppid)
	

if __name__ == '__main__':
  main()
