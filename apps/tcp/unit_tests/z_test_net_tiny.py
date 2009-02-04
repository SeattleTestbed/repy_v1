include tcp.repy

if callfunc == 'initialize':
  IP = getmyip()
  PORT = 12345
  MESSAGE = "hi"
  MAXLEN = 4096

  socket = Connection()
  socket.bind(IP, PORT)

def server():
  socket.listen()
  socket.accept()

  mess = socket.recv(MAXLEN)
  if mess != MESSAGE:
    print "%s != %s" % (mess, MESSAGE)

if callfunc == 'initialize':
  # fork thread for server
  settimer(0, server, ())

  socket.connect(IP, PORT)
  bytes = socket.send(MESSAGE)
  if bytes == 0:
    print "Expected some bytes"

  socket.disconnect()
  exitall()
