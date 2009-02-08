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
  stub.accept()

if callfunc == 'initialize':

  # fork thread for server
  settimer(0, server, ())

  socket = Connection()
  socket.bind(IP, PORT)
  socket.connect(IP, STUB_PORT)

  # shouldn't raise AssertionError
  fn = 'seattle.txt'
  fobj = open(fn, 'r')
  MESS = fobj.read()

  try:
    socket.send(MESS)                               
  except TimeoutError:
    sleep(.01)
    stub.assert_sent_full_window(MESS)
  else:
    raise Exception("should have raised timeout")

  stub.disconnect()
  socket.disconnect()
  exitall()
