def foo(timername):
  mycontext[timername] = True

if callfunc=='initialize':
  mycontext['timetogo'] = False
  myval = settimer(.1,foo,('a'))
  myval = settimer(.1,foo,('b'))
  myval = settimer(.2,foo,('c'))
  sleep(1)
  try:
    if mycontext['a'] and mycontext['b'] and mycontext['c']:
      print "Bye!"
      exitall()
  except KeyError:
    pass
    sleep(2)

  if mycontext['a'] and mycontext['b'] and mycontext['c']:
    print "Bye!"
  raise Exception, "didn't fire after 3 seconds"

