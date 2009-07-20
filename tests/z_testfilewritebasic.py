if callfunc == "initialize":
  fobj = open("junk_test.out", 'w')
  fobj.write("hello")
  fobj.close()

  fobj = open("junk_test.out", 'r')
  if not fobj.read() == "hello":
    print "This shouldn't happen!"

  fobj.close()
