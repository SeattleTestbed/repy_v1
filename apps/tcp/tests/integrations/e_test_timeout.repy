include tcp.repy
include evil_tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  EVIL_PORT = 12346

  evil = EvilConnection()
  evil.bind(IP, EVIL_PORT)
  evil.lurk()

  socket = Connection()
  socket.bind(IP, PORT)
  socket.connect(IP, EVIL_PORT)

  evil.hide()
  # raise TimeoutError
  socket.send("hi")
  exitall()
