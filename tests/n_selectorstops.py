# a test to see if the event used by the socket selector is reclaimed...
def foo(ip,port,sockobj, ch,mainch):
  
  # just wait when getting a connection
  sleep(.1)


def noop():
  pass

def baz():
  print "baz"

if callfunc == 'initialize':
  mycontext['count'] = 0

  ip = getmyip()

  ch1 = waitforconn(ip,12345,foo)
  junk = openconn(ip,12345,foo) 
  stopcomm(ch1)
  stopcomm(junk)
  sleep(1)   # it should be cleaned up now
  settimer(1.0, noop,())
  settimer(.5, exitall,())
  while True:
    try:
      # this should execute before exitall
      settimer(.0, baz,())
      break
    except:
      pass
  


#  sockobj.close()
