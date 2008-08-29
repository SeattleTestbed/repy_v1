def foo():
  raise Exception, "timed out!"

if callfunc=='initialize':
  settimer(0.3, foo, ())
  print "hello, this a lot to print"
  exitall()
