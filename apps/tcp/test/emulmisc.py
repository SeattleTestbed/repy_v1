"""
   Author: Justin Cappos

   Start Date: 19 July 2008

   Description:

   Miscellaneous functions for the sandbox.   Random, exitall, getruntime, 
   etc.
"""

import restrictions
import nanny
import random           # for random.random()
import time             # for time.time()
import nonportable      # for harshexit()
import threading        # for Lock()



# Public interface!
def randomfloat():
  """
   <Purpose>
      Return a random number in the range [0.0, 1.0)

   <Arguments>
      None

   <Exceptions>
      None.

   <Side Effects>
      This function is metered because it may involve using a hardware
      source of randomness.

   <Returns>
      The number (a float)
  """

  restrictions.assertisallowed('randomfloat')
  nanny.tattle_quantity('random',1)

  return random.random()



starttime = time.time()


# Public interface!
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

   <Returns>
      The elapsed time as float
  """

  restrictions.assertisallowed('getruntime')

  return time.time() - starttime



# public interface
def exitall():
  """
   <Purpose>
      Allows the user program to stop execution of the program without
      passing an exit event to the main program. 

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      Interactions with timers and connection / message receiving functions 
      are undefined.   These functions may be called after exit and may 
      have undefined state.

   <Returns>
      None.   The current thread does not resume after exit
  """

  restrictions.assertisallowed('exitall')

  nonportable.harshexit(200)




# public interface
def getlock():
  """
   <Purpose>
      Returns a lock object to the user program.    A lock object supports
      two functions: acquire and release.   See threading.Lock() for details

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      The lock object.
  """

  restrictions.assertisallowed('getlock')

  # I'm a little worried about this, but it should be safe.
  return threading.Lock()

