include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  MAXLEN = 4096

  socket = Connection()
  socket.bind(IP, PORT)

  # Should throw NotConnected exception
  mess = socket.recv(MAXLEN)

  socket.disconnect()
  exitall()
