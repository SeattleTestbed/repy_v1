include stub_tcp.repy
include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  STUB_PORT = 12346
  STUB_WINDOW = 2

  stub = StubConnection()
  stub.bind(IP, STUB_PORT)
  stub.WINDOW = STUB_WINDOW

def server():
  stub.listen()
  stub.accept()

if callfunc == 'initialize':

  # fork thread for server
  settimer(0, server, ())

  socket = Connection()
  socket.bind(IP, PORT)
  socket.connect(IP, STUB_PORT)

  # shouldn't raise AssertionError
  MESS = "hello"

  try:
    socket.send(MESS)                               
  except TimeoutError:
    stub.assert_sent_tiny_window(MESS, STUB_WINDOW)
  else:
    raise Exception("should have raised timeout")

  stub.disconnect()
  socket.disconnect()
  exitall()
