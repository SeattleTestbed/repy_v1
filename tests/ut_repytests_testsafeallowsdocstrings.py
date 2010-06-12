"""
Author: Justin Cappos
Description:
It should be okay to put __ in a doc string...
"""
#pragma repy

def foo():
  """__ should also be allowed here__"""
  pass

class bar:
  """__ and here__"""
  pass
