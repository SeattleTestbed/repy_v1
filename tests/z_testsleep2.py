def foo():
  print "Hi"

if callfunc=='initialize':
  
  myval = settimer(1,foo,())
  sleep(.1)
  canceltimer(myval)
  

