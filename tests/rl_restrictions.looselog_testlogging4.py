def foo(mystr):
  for num in range(100):
    sleep(randomfloat()/100.0)
    print mystr

  mycontext['countlock'].acquire()
  mycontext['threadcount'] = mycontext['threadcount'] -1
  mycontext['countlock'].release()
  
  

if callfunc=='initialize':
  # I *must* be called with a fresh log or else this will not work...

  mycontext['countlock'] = getlock()
  mycontext['threadcount'] = 5

  str1 = 'abcdefgHIJK' # 11 chars
  str2 = 'hijklmnopLM' # 11 chars
  str3 = 'qrstuNOPQRS' # 11 chars
  str4 = 'vwxTUVWXYZ0' # 11 chars
  str5 = 'yz123456789' # 11 chars
  settimer(0, foo, (str1*11,)) 
  settimer(0, foo, (str2*11,))
  settimer(0, foo, (str3*11,))
  settimer(0, foo, (str4*11,))
  settimer(0, foo, (str5*11,))

  while mycontext['threadcount'] > 1:
    sleep(.1)

  mylog = file("experiment.log.old","r")
  logdata = mylog.read()
  mylog.close()

  mylog = file("experiment.log.new","r")
  logdata = logdata + mylog.read()
  mylog.close()

  logdata = logdata[-16 *1024:]  # use the last 16KB

  logdata = logdata.replace(str1,'').strip()
  logdata = logdata.replace(str2,'').strip()
  logdata = logdata.replace(str3,'').strip()
  logdata = logdata.replace(str4,'').strip()
  logdata = logdata.replace(str5,'').strip()
  if len(logdata) >= 11:
    print "Fail",logdata,"Fail"
  else:
    print "Success"
