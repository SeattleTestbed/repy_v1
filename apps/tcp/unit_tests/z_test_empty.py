include tcp.repy
include evil_tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  EVIL_PORT = 12346

  evil = EvilConnection()
  evil.bind(IP, EVIL_PORT)

  socket = Connection()
  socket.bind(IP, PORT)
  socket.listen()
  
  evil.lure(IP, PORT)

  # shouldn't raise CorruptionSuccess
  evil.send_empty_message()

  evil.disappear()
  socket.disconnect()
