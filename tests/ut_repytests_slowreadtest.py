#pragma out
#pragma repy

fo = file("hello.multiline",'r')
settimer(.5,exitall,())
data = fo.read()  # the read won't complete in time because the file's too big
print "Never going to see this!"
