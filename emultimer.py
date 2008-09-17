"""
   Author: Justin Cappos

   Start Date: 29 June 2008

   Description:

   Timer functions for the sandbox.   This does sleep as well as setting and
   cancelling timers.
"""

import threading
import time
import restrictions
import nanny
import idhelper

# for printing exceptions
import tracebackrepy

# for harshexit
import nonportable


timerinfo = {}
# Table of timer structures:
# {'timer':timerobj,'function':function}



# Public interface!
def sleep(seconds):
  """
   <Purpose>
      Allow the current event to pause execution (similar to time.sleep()).
      This function will not return early for any reason

   <Arguments>
      seconds:
         The number of seconds to sleep.   This can be a floating point value

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
  """

  restrictions.assertisallowed('sleep',seconds)
  
  start = time.time()
  sleeptime = seconds
  while sleeptime > 0.0:
    time.sleep(sleeptime)
    sleeptime = (start + sleeptime) - time.time()



# Public interface!
def settimer(waittime, function, args):
  """
   <Purpose>
      Allow the current event to set an event to be performed in the future.
      This does not guarantee the event will be triggered at that time, only
      that it will be triggered after that time.

   <Arguments>
      waittime:
         The minimum amount of time to wait before delivering the event
      function:
         The function to call
      args:
         The arguments to pass to the function.   This should be a tuple or 
         list

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      A timer handle, for use with canceltimer
  """
  restrictions.assertisallowed('settimer',waittime)
  
  eventhandle = idhelper.getuniqueid()

  nanny.tattle_add_item('events',eventhandle)

  tobj = threading.Timer(waittime,functionwrapper,[function] + [eventhandle] + [args])

  timerinfo[eventhandle] = {'timer':tobj}

  # start the timer
  tobj.start()
  return eventhandle
  

# Private function.   This exists to allow me to do quota based items
def functionwrapper(func, timerhandle, args):
  #restrictions ?
  # call the function with the arguments
  try:
    del timerinfo[timerhandle]
  except KeyError:
    # I've been "stopped" by canceltimer
    return
  try:
    func(*args)
  except:
    # Exit if they throw an uncaught exception
    tracebackrepy.handle_exception()
    nonportable.harshexit(30)
    
  # remove the event before I exit
  nanny.tattle_remove_item('events',timerhandle)
  



# Public interface!
def canceltimer(timerhandle):
  """
   <Purpose>
      Cancels a timer.

   <Arguments>
      timerhandle:
         The handle of the timer that should be stopped.   Handles are 
         returned by settimer

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      If False is returned, the timer already fired or was cancelled 
      previously.   If True is returned, the timer was cancelled
  """

  restrictions.assertisallowed('canceltimer')

  try:
    timerinfo[timerhandle]['timer'].cancel()
  except KeyError:
    # The timer already fired (or was cancelled)
    return False

  try:
    del timerinfo[timerhandle]
  except KeyError:
    # The timer just fired (or was cancelled)
    return False
  else:
    # I was able to delete the entry, the function will abort.   I can remove
    # the event
    nanny.tattle_remove_item('events',timerhandle)
    return True
    
