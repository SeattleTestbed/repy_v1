"""
   Author: Justin Cappos

   Start Date: 19 July 2008

   Description:
   
   Provides a unique ID when requested...
   This really should use uniqueid.repy
"""

import threading        # to get the current thread name and a lock


# this dictionary contains keys that are thread names and values that are 
# integers.   The value starts at 0 and is incremented every time we give 
# out an ID.   The ID is formed from those two parts (thread name and ID)
uniqueid_idlist = [0]
uniqueid_idlock = threading.Lock()


def getuniqueid():
  """
   <Purpose>
      Provides a unique identifier.

   <Arguments>
      None

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      The identifier (the string)
  """

  uniqueid_idlock.acquire()

  # I'm using a list because I need a global, but don't want to use the global
  # keyword.   
  myid = uniqueid_idlist[0]
  uniqueid_idlist[0] = uniqueid_idlist[0] + 1

  uniqueid_idlock.release()

  myname = threading.currentThread().getName()

  return myname + ":"+str(myid)
