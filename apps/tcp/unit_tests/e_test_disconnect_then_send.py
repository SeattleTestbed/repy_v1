include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345

  socket = Connection()
  socket.bind(IP, PORT)
  socket.connect(IP, PORT)
  socket.disconnect()

  # should raise NotConnected exception
  socket.send("hi")
