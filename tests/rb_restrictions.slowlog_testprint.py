def foo():
  raise Exception, "timed out!"

if callfunc=='initialize':
  settimer(0.3, foo, ())
  print "hello, this a lot to print in such a short time and even a slow timer should fire"
  exitall()
