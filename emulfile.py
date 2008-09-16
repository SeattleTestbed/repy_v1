"""
   Author: Justin Cappos

   Start Date: 27 June 2008

   Description:

   This is a collection of functions, etc. that need to be emulated in order
   to provide the programmer with a reasonable environment.   This is used
   by repy.py to provide a highly restricted (but usable) environment.
"""

import restrictions
import nanny
# needed for listdir and remove
import os 
import idhelper

# I need to rename file so that the checker doesn't complain...
myfile = file

# PUBLIC
def listdir():
  """
   <Purpose>
      Allows the user program to get a list of files in their area.

   <Arguments>
      None

   <Exceptions>
      This probably shouldn't raise any errors / exceptions so long as the
      node manager isn't buggy.

   <Side Effects>
      None

   <Returns>
      A list of strings (file names)
  """

  restrictions.assertisallowed('listdir')

  return os.listdir('.')
   

# PUBLIC
def removefile(filename):
  """
   <Purpose>
      Allows the user program to remove a file in their area.

   <Arguments>
      filename: the name of the file to remove.   It must not contain 
      characters other than 'a-zA-Z0-9.-_' and cannot be '.' or '..'

   <Exceptions>
      This probably shouldn't raise any errors / exceptions so long as the
      node manager isn't buggy.

   <Side Effects>
      None

   <Returns>
      A list of strings (file names)
  """

  restrictions.assertisallowed('removefile')

  assert_is_allowed_filename(filename)
  
  # Problem notification thanks to Andrei Borac
  # Handle the case where the file is open via an exception to prevent the user
  # from removing a file to circumvent resource accounting

  for filehandle in fileinfo:
    if filename == fileinfo[filehandle]['filename']:
      raise Exception, 'File "'+filename+'" is open with handle "'+filehandle+'"'
  return os.remove(filename)
   




# PUBLIC
def emulated_open(filename, mode="r"):
  """
   <Purpose>
      Allows the user program to open a file safely.   This function is meant
      to resemble the builtin "open"

   <Arguments>
      filename:
         The file that should be operated on
      mode:
         The mode (see open)

   <Exceptions>
      As with open, this may raise a number of errors

   <Side Effects>
      Opens a file on disk, using a file descriptor.   When opened with "w"
      it will truncate the existing file.

   <Returns>
      A file-like object 
  """

  restrictions.assertisallowed('open',filename,mode)

  return emulated_file(filename, mode)
   


# This keeps the state for the files (the actual objects, etc.)
fileinfo = {}



# private.   Checks the filename for disallowed characters
def assert_is_allowed_filename(filename):

  # file names must contain *only* these chars
  filenameallowedchars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-'

  # I should check to see if the filename is allowed.   I'm going to do
  # this here.  
  if type(filename) != str:
    raise TypeError, "filename is not a string!"

  # among other things, this avoids them putting / or \ in the filename
  for char in filename:
    if char not in filenameallowedchars:
      raise TypeError, "filename has disallowed character '"+char+"'"
 
  # Should I do anything more rigorous?   I.e. check for links, etc.?
  if filename == "." or filename == '..':
    raise TypeError, "filename cannot be a directory"




# PUBLIC class.  The user can mess with this...
class emulated_file:
  """
    A safe file-like class that resembles the builtin file class.
    The functions in this file are essentially identical to the builtin file
    class

  """

  # This is an index into the fileinfo table...

  filehandle = None

  # I do not use these.   This is merely for user / API convenience
  mode = None
  name = None
  softspace = 0

  def __init__(self, filename, mode="r"):
    restrictions.assertisallowed('file.__init__',filename,mode)
   
    assert_is_allowed_filename(filename)

    self.filehandle = idhelper.getuniqueid()

    nanny.tattle_add_item('filesopened',self.filehandle)

    fileinfo[self.filehandle] = {'filename':filename, 'mode':mode,'fobj':myfile(filename,mode)}
    self.name=filename
    self.mode=mode
    return None 


  # We are iterable!
  def __iter__(self):
    return self


#
# Do most of the normal file calls by checking them and passing them through
#

  def close(self):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.close')

    # Ignore multiple closes (as file does)
    if myfilehandle not in fileinfo:
      return

    nanny.tattle_remove_item('filesopened',myfilehandle)

    returnvalue = fileinfo[myfilehandle]['fobj'].close()

    # delete the filehandle
    del fileinfo[myfilehandle]

    return returnvalue



  def flush(self):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.flush')

    return fileinfo[myfilehandle]['fobj'].flush()


  def next(self):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.next')

    return fileinfo[myfilehandle]['fobj'].next()



  def read(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.read',*args)

    # wait if it's already over used
    nanny.tattle_quantity('fileread',0)

    readdata = fileinfo[myfilehandle]['fobj'].read(*args)

    nanny.tattle_quantity('fileread',len(readdata))

    return readdata


  def readline(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.readline',*args)

    # wait if it's already over used
    nanny.tattle_quantity('fileread',0)

    readdata =  fileinfo[myfilehandle]['fobj'].readline(*args)

    nanny.tattle_quantity('fileread',len(readdata))

    return readdata


  def readlines(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.readlines',*args)

    # wait if it's already over used
    nanny.tattle_quantity('fileread',0)

    readlist = fileinfo[myfilehandle]['fobj'].readlines(*args)
    readamt = 0
    for readitem in readlist:
      readamt = readamt + len(str(readitem))

    nanny.tattle_quantity('fileread',readamt)

    return readlist


  def seek(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.seek',*args)

    return fileinfo[myfilehandle]['fobj'].seek(*args)


  def write(self,writeitem):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.write',writeitem)

    # wait if it's already over used
    nanny.tattle_quantity('filewrite',0)

    retval = fileinfo[myfilehandle]['fobj'].write(writeitem)

    writeamt = len(str(writeitem))
    nanny.tattle_quantity('filewrite',writeamt)

    return retval


  def writelines(self,writelist):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.writelines',writelist)

    # wait if it's already over used
    nanny.tattle_quantity('filewrite',0)

    retval = fileinfo[myfilehandle]['fobj'].writelines(writelist)
    writeamt = 0
    for writeitem in writelist:
      writeamt = writeamt + len(str(writeitem))

    nanny.tattle_quantity('filewrite',writeamt)
    return retval


# End of emulated_file class

