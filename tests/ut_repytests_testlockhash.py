#pragma repy

"""
  Locks should not be hashable...
"""

if callfunc == "initialize":
  mylock = getlock()

  mydict = {}
  try:
    mydict[mylock] = 7
  except AttributeError:
    # I should get an exception here...
    pass
  else:
    print 'locks are hashable!'

