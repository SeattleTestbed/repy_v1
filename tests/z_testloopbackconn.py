def foo(ip,port,sockobj, ch,mainch):
  
  data = sockobj.recv(4096)

  if data != "Hello":
    print 'Error: data did not match "Hello"'
    exitall()

  sockobj.send("bye")

  stopcomm(mainch)
  stopcomm(ch)


if callfunc == 'initialize':
  waitforconn('127.0.0.1',12345,foo)
  sleep(.2)
  sockobj = openconn('127.0.0.1',12345)

  sockobj.send("Hello")

  data = sockobj.recv(4096)

  if data != "bye":
    print 'Error: data did not match "bye"'
    exit(1)

  sockobj.close()
