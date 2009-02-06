include evil_tcp.repy
include tcp.repy

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  EVIL_PORT = 12346
  socket = Connection()
  socket.bind(IP, PORT)

def server():
  socket.listen()
  socket.accept()

if callfunc == 'initialize':
  # fork thread for server
  settimer(0, server, ())

  evil = EvilConnection()
  evil.bind(IP, EVIL_PORT)
  
  evil.lure(IP, PORT)

  # shouldn't raise CorruptionSuccess
  evil.send_empty_message()

  evil.disappear()
  socket.disconnect()
  exitall()
