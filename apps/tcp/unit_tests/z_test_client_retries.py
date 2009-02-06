include tcp.repy

def callback(ip, port, mess, ch):
#  packet = unpack(mess)
  mycontext['tries'] += 1

if callfunc == 'initialize':
  IP = '127.0.0.1' #  getmyip()
  PORT = 12345
  TIMEOUT = .1
  RETRIES = 4
  MESSAGE = "hi"
  WINDOW = 10
  SEQ_NUM = 0

  mycontext['tries'] = 0
  server = recvmess(IP, PORT, callback)

  socket = TcpClient()
  socket.reset(SEQ_NUM, WINDOW)
  try:
    bytes = socket.send(MESSAGE, IP, PORT, IP, PORT, RETRIES, TIMEOUT)
    if bytes == 0:
      print "Expected some bytes"
  except TimeoutError:
    sleep(.01)
  else:
    stopcomm(server)
    raise

  assert mycontext['tries'] == (RETRIES + 1)

  stopcomm(server)
  exitall()
