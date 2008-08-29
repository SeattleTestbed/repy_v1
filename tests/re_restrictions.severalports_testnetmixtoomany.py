def bar(ip,port,mess, ch):
  
  # just wait when getting a connection
  sleep(.1)


def foo(ip,port,sockobj, ch,mainch):
  
  # just wait when getting a connection
  sleep(.1)


if callfunc == 'initialize':
  mycontext['count'] = 0

  ip = getmyip()

  ch1 = waitforconn(ip,12345,foo)
  ch2 = recvmess(ip,12346,bar)
  ch3 = waitforconn(ip,12347,foo) # should be an error, insockets > 2
  sleep(.1)
  stopcomm(ch1)
  stopcomm(ch2)
  stopcomm(ch3)

#  sockobj.close()
