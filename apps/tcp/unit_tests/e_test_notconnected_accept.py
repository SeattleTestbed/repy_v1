include tcp.repy

if callfunc == 'initialize':
  IP = getmyip()
  PORT = 12345
  MESSAGE = "hi"
  MAXLEN = 4096

  socket = Connection()
  socket.bind(IP, PORT)

  # raise notconnected
  socket.accept()
  exitall()
