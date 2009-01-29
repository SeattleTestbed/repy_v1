include stub_tcp.repy
include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  STUB_PORT = 12346

  stub = StubConnection()
  stub.bind(IP, STUB_PORT)

  socket = Connection()
  socket.bind(IP, PORT)
  socket.listen()
  
  stub.connect(IP, PORT)

  # shouldn't raise AssertionError
  stub.assert_cumulative_acking()

  stub.disconnect()
  socket.disconnect()
