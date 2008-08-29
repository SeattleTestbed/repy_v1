def foo(ip,port,sockobj, ch,mainch):
  
  # just wait when getting a connection
  sleep(.1)

  # this is so a bad test will eventually exit...
  mycontext['count'] = mycontext['count']  + 1
  if mycontext['count'] == 3:
    stopcomm(ch)
    stopcomm(mainch)


if callfunc == 'initialize':
  mycontext['count'] = 0

  ip = getmyip()

  waitforconn(ip,12345,foo)
  sleep(.1)
  sockobj  = openconn(ip,12345)
  sockobj2 = openconn(ip,12345)
  sockobj3 = openconn(ip,12345) 
  sockobj4 = openconn(ip,12345)
  sockobj5 = openconn(ip,12345)
  sockobj6 = openconn(ip,12345)# should be an error (too many outsockets)

#  sockobj.close()
