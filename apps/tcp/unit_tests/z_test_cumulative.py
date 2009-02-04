include stub_tcp.repy
include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  STUB_PORT = 12346

  socket = Connection()
  socket.bind(IP, PORT)


def server():
  socket.listen()
  socket.accept()
  
if callfunc == 'initialize':
  # fork thread for server
  settimer(0, server, ())

  stub = StubConnection()
  stub.bind(IP, STUB_PORT)
  stub.connect(IP, PORT)

  # shouldn't raise AssertionError
  stub.assert_cumulative_acking()

  stub.disconnect()
  socket.disconnect()
  exitall()

