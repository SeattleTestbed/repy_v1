writedata = ['foo\n','bar\n','baz\n']

fo = file("junk_test.out",'w')
fo.writelines(writedata)
fo.close()

fo = file("junk_test.out",'r')
data = fo.readlines()
fo.close()

print writedata==data
