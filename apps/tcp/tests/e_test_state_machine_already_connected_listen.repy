include tcp.repy

if callfunc == 'initialize':
  IP = getmyip()
  PORT = 12345

  socket = TcpStateMachine()

def server():
  # raise already connected
  socket.connect(IP, PORT, IP, PORT)

if callfunc == 'initialize':
  # fork thread for server
  settimer(0, server, ())
  sleep(.01)

  try:
    socket.listen()
  except AlreadyConnectedError:
    raise
  else:
    print "should have raise already connected"

  exitall()
