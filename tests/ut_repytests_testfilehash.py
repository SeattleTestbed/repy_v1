#pragma repy

"""
  Files should not be hashable...
"""

if callfunc == "initialize":
  myfileobj = file('junk_test.out','w')

  try:
    mydict = {}
    try:
      mydict[myfileobj] = 7
    except AttributeError:
      # I should get an exception here...
      pass
    else:
      print 'files are hashable!'

  finally:
    myfileobj.close()
    removefile('junk_test.out')
