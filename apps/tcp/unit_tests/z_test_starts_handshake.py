include stub_tcp.repy
include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  STUB_PORT = 12346

  stub = StubConnection()
  stub.bind(IP, STUB_PORT)

def server():
  stub.listen()

if callfunc == 'initialize':
  # fork thread for server
  settimer(0, server, ())

  socket = Connection()
  socket.bind(IP, PORT)

  # shouldn't raise AssertionError
  try:
    socket.connect(IP, STUB_PORT)
  except TimeoutError:
    sleep(.01)
    stub.assert_sent_syn()
  else:
    raise Exception("should have raised timeout")

  stub.disconnect()
  socket.disconnect()
  exitall()
