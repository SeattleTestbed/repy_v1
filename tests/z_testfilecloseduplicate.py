fobj = open("junk_test.out")
fobj.close()
if fobj.close():
  print "a duplicate fobj.close() should return false"
