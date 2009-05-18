# Test attempts to call openconn with a very small timeout to test its behavior

if callfunc == "initialize":
  try:
    # This should timeout
    openconn("JUNKHOST!!!!",12345,timeout=0.0000000001)
  except Exception,e:
    if "timed" in str(e) or "Timed" in str(e):
      pass
    else:
      print "Unexpected error! Should timeout.",str(e)



