if callfunc == "initialize":
  try:
    fobj = open("junk_test.out", 'r')
    fobj.flush()
    # flush on a read-only file should be a no-op
  finally:
    fobj.close()
