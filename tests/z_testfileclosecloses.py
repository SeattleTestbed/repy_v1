fobj = open(filename)
fobj.close()
try:
  fobj.read(1)
except:
  pass
else:
  print "We shouldn't be able to read from closed files"
