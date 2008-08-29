def foo(ip,port,sockobj, ch,mainch):
  raise Exception, "Should not be here"

def noop(ip, port, sockobj, ch, mainch):
  stopcomm(ch)
  stopcomm(mainch)
  

if callfunc == 'initialize':

  ip = getmyip()

  waitforconn(ip,12345,foo)
  waitforconn(ip,12345,noop)  # should overwrite foo...
  sleep(.1)
  sockobj = openconn(ip,12345)

  sockobj.close()
