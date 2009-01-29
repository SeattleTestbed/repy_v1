include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  fn = "seattle.txt"
  fobj = open(fn, "r")
  
  MESSAGE = fobj.read()
  MAXLEN = 1000000 # all of it
  socket = Connection()
  socket.bind(IP, PORT)
  socket.connect(IP, PORT)

  bytes = socket.send(MESSAGE)
  if bytes == 0:
    print "Expected some bytes"

  mess = socket.recv(MAXLEN)
  if mess != MESSAGE:
    print "%s != " % mess
    print "%s" % MESSAGE


  socket.disconnect()
