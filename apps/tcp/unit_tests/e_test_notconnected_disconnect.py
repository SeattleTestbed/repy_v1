include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345

  socket = Connection()
  socket.bind(IP, PORT)

  # should raise NotConnected exception
  socket.disconnect()
  exitall()
