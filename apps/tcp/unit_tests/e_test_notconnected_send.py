include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  MESSAGE = "hi"
  MAXLEN = 4096

  socket = Connection()
  socket.bind(IP, PORT)

  # should raise NotConnected exception
  bytes = socket.send(MESSAGE)

  socket.disconnect()
  exitall()
