def foo(ip,port,sockobj, ch,mainch):
  
  stopcomm(mainch)
  # I don't close this connection's commhandle


if callfunc == 'initialize':

  ip = getmyip()

  waitforconn(ip,12345,foo)
  sleep(.1)
  sockobj = openconn(ip,12345)

  settimer(1, sockobj.close,())
  try:
    data = sockobj.recv(4096)
    print "Error, should get an exception..."
  except Exception:
    pass

