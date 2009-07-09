if callfunc == "initialize":
  fobj = open("junk_test.out", 'rb')
  fobj.read()
  fobj.seek(0)
  fobj.read(-1)
