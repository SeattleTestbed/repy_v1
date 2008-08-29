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

  ch1 = waitforconn(ip,12345,foo)
  ch2 = waitforconn(ip,12346,foo)
  ch3 = waitforconn(ip,12347,foo) # should be an error because allowed only 2 
  sleep(.1)
  stopcomm(ch1)
  stopcomm(ch2)
  stopcomm(ch3)

#  sockobj.close()
