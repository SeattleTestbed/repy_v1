include stub_tcp.repy
include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  STUB_PORT = 12346

def server():
  socket = Connection()
  socket.bind(IP, PORT)
  try:
    socket.listen()
    socket.accept()
  except:
    pass
  socket.disconnect()

if callfunc == 'initialize':

  stub = StubConnection()
  stub.bind(IP, STUB_PORT)

  # fork a thread to server
  settimer(0, server, ())

  # shouldn't raise error
  stub.assert_responds_to_syn(IP, PORT)
  stub.disconnect()
  exitall()

