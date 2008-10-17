""" 
Author: Justin Cappos

Start Date: July 4th, 2008

Description:
Is the nanny for cpu on Windows.   This uses pssuspend and pskill
(both are a pain in the ass) to do the actual work...


"""


import os
import time
import sys
import tracebackrepy

# used to stop the process
import subprocess

# used to get information about the process we're tracking
import win32con
import win32api
import win32process








winlastcpuinfo = [0,0]
firststart = None
firstcpu = None

# Keep track of info for rolling average
totaltime = 0.0
totalcpu = 0.0

def win_check_cpu_use(phandle, cpulimit,pid):
  global firststart
  global firstcpu
  global winlastcpuinfo
  global totaltime, totalcpu

  # get use information and time...
  now = time.time()
  usedata = win32process.GetProcessTimes(phandle)

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
  #  print (usertime - firstcpu) / (now - firststart), percentused, now
  # print (totalcpu/totaltime), percentused, elapsedtime, totalcpu, totaltime

  # they have been well behaved!   Do nothing
  if (totalcpu/totaltime) <= cpulimit:
     return 0

  # stop the process
  # Measure the delay in executution to compensate in the stoptime
  pretime = time.time()
  exec_commandlist(["pssuspend.exe","/accepteula",str(pid)])
  delay = time.time() - pretime

  # sleep to delay processing (see note in nonportable for where this formula 
  # comes from)
  #stoptime = ((percentused / cpulimit)-1) * elapsedtime * 2
  # Base new stoptime on average cpu, and add pause delay to compensate
  stoptime = ((totalcpu/totaltime) - cpulimit) * totaltime * 2 + delay

  # print "Stopping: ", stoptime, " Delay: ", delay
  time.sleep(stoptime)

  # continue the process
  exec_commandlist(["pssuspend.exe","/accepteula","-r",str(pid)])

  # Return how long we slept so parent knows whether it should sleep
  return stoptime
  


def exec_commandlist(commandlist):
  # I don't think we need to do any sort of clean up after the process exits...
  # they are chatty programs and it's tough to tell what is happening with
  # them.   I'll leave them be
  # Modified to execute commands at High priority, done because otherwise it
  # takes too long to pause and restart the process
  p = subprocess.Popen(commandlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags= win32con.HIGH_PRIORITY_CLASS)
  # NOTE: For some reason Vista seems to hang sometimes after a SIGCONT 
  # (perhaps the signal isn't delivered).   Reading stdout and stderr seems to
  # fix this.   I'm unsure why, but I speculate the process was being 
  # terminated before it finished (perhaps because of closing stdout or stderr 
  # early)

  # This seems to greatly reduce overhead, but we may need to test this
  # return

  p.stdout.read()
  p.stderr.read()
  p.stdout.close()
  p.stderr.close()

  

  


def main():

  if len(sys.argv) != 4:
    print "Error, didn't get the right number of args:",sys.argv
    sys.exit(1)

  ppid = int(sys.argv[1])
  limit = float(sys.argv[2])
  freq = float(sys.argv[3])

  try:
    phandle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION,0,ppid)
  except win32api.error, e:
    # "The parameter is incorrect.".   We get this when the process has exited
    # already...
    if e[0]==87:
      sys.exit(0)
    raise
    

  # run forever, checking the process' memory use and stopping when appropriate
  try:
    while True:
	  # Base amount of sleeping on return value of 
	  # win_check_cpu_use to prevent under/over sleeping
      slept = win_check_cpu_use(phandle, limit, ppid)
      if slept == 0:
        time.sleep(freq)
      elif (slept < freq):
        time.sleep(freq-slept)
    
      # see if the process exited...
      status = win32process.GetExitCodeProcess(phandle)
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
#      exec_commandlist(["pskill.exe","/accepteula","-t",str(ppid)])
    exec_commandlist(["pskill.exe","/accepteula",str(ppid)])
      



if __name__ == '__main__':
  main()
