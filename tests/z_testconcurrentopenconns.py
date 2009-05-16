
if callfunc == "initialize":
  ip = getmyip()
  port = 12345
  remoteip = gethostbyname_ex("google.com")[2][1]
  remoteport = 80
  
  # First openconn should work fine
  try:
    sock1 = openconn(remoteip, remoteport, ip, port)
  except Exception, e:
    print "Unexpected Exception! '"+str(e)+"'"
    exitall()
  
  # This should fail, sock1 is open
  try:
    sock2 = openconn(remoteip, remoteport, ip, port)
  except:
    # This is expected
    pass
  else:
    print "Unexpectedly created a new socket! Reused network tuple!"  
    sock2.close()

  # Close the socket, now re-try. openconn should block until the socket is available
  sock1.close()
  
  # This should block, but we eventually get the socket
  try:
    sock2 = openconn(remoteip, remoteport, ip, port)
  except Exception, e:
    print "Unexpected exception! '"+str(e)+"'.   We should block execution!"
  else:  
    sock2.close()


