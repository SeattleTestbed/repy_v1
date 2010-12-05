#pragma repy

"""
  Sockets should not be hashable...
"""

# Handle a new connection
def new_conn(ip,port,sock,ch1,ch2):
  stopcomm(ch2)

if callfunc == "initialize":
  # Get the ip
  ip = getmyip()

  # Setup listener
  waitforconn(ip,<connport>,new_conn)

  # Connect
  sock = openconn(ip,<connport>)

  mydict = {}
  try:
    mydict[sock] = 7
  except AttributeError:
    # I should get an exception here...
    pass
  else:
    print 'sockets are hashable!'

  sock.close()

