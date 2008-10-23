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
  import windows_ce_api
  windowsAPI = windows_ce_api
  pass

winlastcpuinfo = [0,0]
firststart = None
firstcpu = None

# Keep track of info for rolling average
totaltime = 0.0
totalcpu = 0.0

def win_check_cpu_use(cpulimit,pid):
  global firststart
  global firstcpu
  global winlastcpuinfo
  global totaltime, totalcpu

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

  # Increment total time
  totaltime += elapsedtime 
  # Increment CPU use
  if ((totalcpu/totaltime) >= cpulimit):
    totalcpu += (usertime - oldusertime) # Don't apply max function, allow the average to drop
  else:
    # Set a minimum for percentused, enfore a use it or lose it policy
	totalcpu += max(percentused, cpulimit)*elapsedtime

  # Useful debugging information...  
  #print (totalcpu/totaltime), percentused, elapsedtime, totalcpu, totaltime

  # they have been well behaved!   Do nothing
  if (totalcpu/totaltime) <= cpulimit:
     return 0

  # sleep to delay processing 
  # stoptime = ((percentused / cpulimit)-1) * elapsedtime * 2
  # Base new stoptime on average cpu, and add pause delay to compensate
  stoptime = ((totalcpu/totaltime) - cpulimit) * totaltime * 2

  #print "Stopping: ", stoptime
  # Call new api to suspend/resume process and sleep for specified time
  windowsAPI.timeoutProcess(pid, stoptime)

  # Return how long we slept so parent knows whether it should sleep
  return stoptime

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
      if slept == 0:
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

  except:
    tracebackrepy.handle_exception()
    print >> sys.stderr, "Win nanny died!   Trying to kill everything else"
    
    # kill the program we're monitoring
    # Use newer api to kill process
    windowsAPI.killProcess(ppid)
	

if __name__ == '__main__':
  main()
