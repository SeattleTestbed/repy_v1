"""
<Program Name>
  tr_convertfiles.py

<Started>
  March, 2011

<Author>
  Lukas Puehringer, University of Vienna
  lukas.puehringer@univie.ac.at

<Purpose>
  Flattens out the 'web' directory and copies all its files to the 'build'
  directory, representing the username 'system' and each file's relative path
  to the base64 encoded filename.

"""


import os
import sys
import base64
import shutil

global basepath
global savepath

def flat_out(path):
  
  for item in os.listdir(path):
    # Filter out hidden directories
    if item.find('.',0,1) == -1:
      newpath = path +"/"+ item
      
      if os.path.isdir(newpath):
        # If the item is directory call flat_out for it.
        flat_out(newpath)
      
      else:
        # Else create the new filename.
        virtual_filename = "system" + str(newpath.replace(basepath + "/", ''))
        
        # Encode the filename
        encoded_filename = base64.b64encode(virtual_filename, '-_')
        encoded_filename = encoded_filename.replace('=', '.')
        
        # Copy the Filename to the build directory
        shutil.copyfile(newpath, savepath+'/'+ encoded_filename)

        

if __name__ == "__main__":

  usage = "There has to be a directory 'web' and 'build' in this directory."
  
  print "Copying files recursivly from 'web' to 'build' directory."
  print "Converting filenames"
  
  # This directory contains all webfiles HTML, JS, CSS
  basedir = "web"
  
  # To this directory the name converted files web files will be saved
  savedir = "build"
    
  if os.path.isdir(basedir) and os.path.isdir(savedir):
    pass
  else:
    print usage
    exit()
  
  basepath = os.path.abspath(basedir)
  savepath = os.path.abspath(savedir)

  # Flat out on convert filenames recursively
  try:
    flat_out(basepath)
  except Exception, e:
    print "Something went wrong in flating out the web directory: " + str(e)
  
  

