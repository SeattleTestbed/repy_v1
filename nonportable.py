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

# used to query status, etc.
import subprocess

# used for select (duh)
import select

# used for socket.error
import socket

# need for status retrieval
import statusstorage

# needed to check disk usage
import misc


# This prevents writes to the nanny's status information after we want to stop
statuslock = threading.Lock()

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
  elif ostype == 'Windows':
    # stderr is not automatically flushed in Windows...
    sys.stderr.flush()
    os._exit(val)
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"
  


def monitor_cpu_disk_and_mem(cpuallowed, diskallowed, memallowed):

  if ostype == 'Linux' or ostype == 'Darwin':
    # The frequency constant here seems to effect the "burstiness" of the
    # cpu use but not the overall amount.
    do_forked_monitor(.1, cpuallowed, diskallowed, memallowed)

  elif ostype == 'Windows':
    frequency = .2 # I tried .1 and I ended up killing the process...

    # start the CPU nanny and tell them our pid and limit...
    # NOTE: Is there a better way?
    if os.path.exists('..\python') or os.path.exists('..\python.exe'):
      pythonpath = '..\python'
    else:
      pythonpath = 'python'

    # NOTE: always run the cpu nanny from the current dir.   I think this is
    # correct, but I may need to change based upon the python path
    nannypath = 'win_cpu_nanny.py'
   
    cpu_nanny_cmd = pythonpath+" "+nannypath+" "+str(os.getpid())+" "+str(cpuallowed)+" "+str(frequency)
    # need to set the cwd so that we know where to find it.   Let's assume it's
    # in the same directory we are in
    nannydir = os.path.dirname(sys.argv[0])
  
    # fix it if there is no dir...
    if nannydir == '':
      nannydir="."

    # execute the nanny...
    junkprocessinfo = subprocess.Popen(cpu_nanny_cmd, cwd=nannydir)
    # our nanny should outlive us, so it's okay to leave it alone...


    # now we set up a memory / disk thread nanny...
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


###################     Windows specific functions   #######################

try:
  import win32con
  import win32api
  import win32process
except ImportError:
  pass


def win_check_memory_use(phandle, memlimit):


  # use the process handle to get the memory info
  meminfo = win32process.GetProcessMemoryInfo(phandle)

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

  diskused = misc.compute_disk_use(".")

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
    # I need a process handle to get information (like memory use, etc.)
    mypid = os.getpid()
    myphandle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION,0,mypid)

    # run forever (only exit if an error occurs)
    while True:
      try:
        time.sleep(self.frequency)
        win_check_disk_use(self.diskallowed)
        win_check_memory_use(myphandle, self.memallowed)

        # prevent concurrent status file writes.   
        statuslock.acquire()
        try: 
          # write out status information
          statusstorage.write_status("Started")

        finally:
          # must release before harshexit...
          statuslock.release()

      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "Nanny died!   Trying to kill everything else"
        harshexit(20)





      
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
        print >> self.fileobj, repr(list(os.times())+ [time.time()])
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



# Keep track of info for rolling average
totaltime = 0.0 # Might be issue if user uptime > DBL_MAX or 10^298 centuries
totalcpu = 0.0 

# this ensures that the CPU quota is actually enforced on the client
def enforce_cpu_quota(readfobj, cpulimit, frequency, childpid):
  global totaltime, totalcpu

  elapsedtime, percentused = get_time_and_cpu_percent(readfobj)

  # They get a free pass (likely their first or last time)
  if elapsedtime == 0.0:
    return
  
  # Increment total time
  totaltime += elapsedtime 
  # Increment CPU use
  if ((totalcpu/totaltime) >= cpulimit):
    totalcpu += percentused*elapsedtime # Don't apply max function, allow the average to drop
  else:
    # Set a minimum for percentused, enfore a use it or lose it policy
	totalcpu += max(percentused, cpulimit)*elapsedtime
	
  #print (totalcpu/totaltime), percentused, elapsedtime, totaltime, totalcpu

  # If average CPU use is fine, then continue
  if (totalcpu/totaltime) <= cpulimit:
     time.sleep(frequency) # If we don't sleep, this process burns cpu doing nothing
     return

  # They must be punished by stopping
  os.kill(childpid, signal.SIGSTOP)

  # we'll stop them for at least long enough to even out the damage

  # why does this formula work?  Where does *2 come from?
  # I checked and sleep is sleeping the full time...
  # I've verified the os.times() data tracks perfectly...
  # I've tried it will different publishing frequencies and it works...
  # this formula works for different cpulimits as well
  # for very low sleep rates, this doesn't work.   The time is way over.
  # for high sleep rates, this works fine.
  # Old Stop Time
  #stoptime = (((percentused-cpulimit) / cpulimit)-1) * elapsedtime * 2

  # New stoptime
  # Determine how far over the limit the average, and punish progressively
  # Also, unsure about the *2 but it does seem to work....
  stoptime = ((totalcpu/totaltime) - cpulimit) * totaltime * 2
 
  # Sanity Check
  # There is no reason to punish a process for more than
  # frequency / cpulimit
  # BECAUSE that means that if a process uses 100% during a sampling interval,
  # the resulting stop+use interval should average to the CPU limit
  # stoptime = min(frequency/cpulimit, stoptime)

  #print "Stopping: ", stoptime
  time.sleep(stoptime)

  # And now they can start back up!
  os.kill(childpid, signal.SIGCONT)

  # If stoptime < frequency, then we would over-sample if we don't sleep
  if (stoptime < frequency):
    time.sleep(frequency-stoptime)
  
  

lastenforcedata = None
junkfirst = 0
junkstart = time.time()

def get_time_and_cpu_percent(readfobj):
  global lastenforcedata
  global junkfirst

  cpudata = readfobj.readline().strip()
    

  # the child must have exited, I'll return so I can wait on them...
  if not cpudata:
    return (0.0, 0.0)

  quotainfo = eval(cpudata)

  # Give them a free pass the first time
  if not lastenforcedata:
    lastenforcedata = quotainfo
    junkfirst = quotainfo[4]
    return (0.0, 0.0)


  # The os.times() info is: (cpu, sys, child cpu, child sys, current time)
  # I think it makes the most sense to use the combined cpu/sys time as well
  # as the current time...
  cputime = quotainfo[0]
  systime = quotainfo[1]
  childcputime = quotainfo[2]
  childsystime = quotainfo[3]
  clocktime = quotainfo[4] 	# processor time (it's in the wrong units...)
  currenttime = quotainfo[5]

  usertime = cputime + systime

  # How can they have a child?
  if childcputime != 0.0 or childsystime != 0.0:
    raise Exception, "Non zero child time!: Cpu time '"+str(childcputime)+"' > Sys time '"+str(childsystime)+"'"

  oldusertime = lastenforcedata[0] + lastenforcedata[1]
  oldclocktime = lastenforcedata[4]
  oldcurrenttime = lastenforcedata[5]

  # NOTE: Processor time is going backwards...   Is this possible?   
  # Should do something nicer like ignore quota?
  if clocktime < oldclocktime:
    raise Exception, "Elapsed time '"+str(currenttime)+"' less than previous '"+str(oldcurrenttime)+"'"

  # user time is going backwards...   I don't think this is possible
  if usertime < oldusertime:
    raise Exception, "User time '"+str(usertime)+"' at '"+str(currenttime)+"' less than user time '"+str(oldusertime)+"' at '"+str(oldcurrenttime)+"'"


  percentused = (usertime - oldusertime) / (clocktime - oldclocktime)

  lastenforcedata = quotainfo

  #print (usertime) / (clocktime - junkfirst), percentused, usertime, time.time() - junkstart
  #print percentused, usertime, oldusertime, clocktime, oldclocktime, clocktime-oldclocktime
  sys.stdout.flush()
  return (currenttime - oldcurrenttime, percentused)
  
  

# see if the process is over quota and if so terminate with extreme prejudice.
def enforce_disk_quota(disklimit, childpid):

  diskused = misc.compute_disk_use(".")

  if diskused > disklimit:
    os.kill(childpid, signal.SIGKILL)
    raise Exception, "Terminated child '"+str(childpid)+"' with disk use '"+str(diskused)+"' with limit '"+str(disklimit)+"'"
  
  

    

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
  p = subprocess.Popen(memorycmd, shell=True, stdout=subprocess.PIPE, 
	stderr=subprocess.PIPE, close_fds=True)

  cmddata = p.stdout.read()
  p.stdout.close()
  errdata = p.stderr.read()
  p.stderr.close()
  junkstatus = os.waitpid(p.pid,0)

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
      os.kill(childpid, signal.SIGKILL)
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
      os.kill(childpid, signal.SIGKILL)
      raise Exception, "Terminated child '"+str(childpid)+"' with memory use '"+str(memoryused)+"' with limit '"+str(memorylimit)+"'"
  
  

  elif cmddata == '' and 'proc' in errdata:
    # PlanetLab /proc error case.   May show up in other environments too...
    # this is the number of consecutive times I've seen this error.
    badproccount = badproccount + 1
    if badproccount > 3:
      raise Exception, "Memory restriction thread had three consecutive /proc errors"
 
  else:
    raise Exception, "Cannot understand '"+memorycmd+"' output: '"+cmddata+"'"


  

  


def do_forked_monitor(frequency, cpulimit, disklimit, memlimit):
  # Test only, override frequency
  #frequency = 0.25

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

        # let's check the process and make sure it's not over quota.  
        enforce_cpu_quota(myreadpipe, cpulimit, frequency, childpid)

        # let's check the process and make sure it's not over quota.  
        enforce_disk_quota(disklimit, childpid)

        # let's check the process and make sure it's not over quota.  
        enforce_memory_quota(memlimit, childpid)

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


  

# Call init_ostype!!!
init_ostype()
