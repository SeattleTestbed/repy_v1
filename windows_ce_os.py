# From http://www.nabble.com/Can-I-execute-external-programs-from-PythonCe--td19307784.html
# Allows for system calls on Windows CE

from ctypes import * 
import os 

CreateProcess = cdll.coredll.CreateProcessW 
WaitForSingleObject = cdll.coredll.WaitForSingleObject 
GetExitCodeProcess = cdll.coredll.GetExitCodeProcess 
DWORD = HANDLE = c_ulong 

class _PI(Structure): 
    _fields_ = [('hPro', HANDLE), 
                ('hTh', HANDLE), 
                ('idPro', DWORD), 
                ('idTh', DWORD)] 
    
def _create_process(cmd, args): 
    pi = _PI() 
    CreateProcess(unicode(cmd), 
                  unicode(args), 
                  0, 
                  0, 
                  0, 
                  0, 
                  0, 
                  0, 
                  0, 
                  byref(pi)) 
                  
    return pi.hPro 
    
def _wait_process(hPro): 
    WaitForSingleObject(hPro, c_ulong(0xffffffff)) 
    return GetExitCodeProcess(hPro) 
    
def _quote(s): 
    if " " in s: 
        return '"%s"' %s 
    return s 
    
def execv(path, args): 
    if not type(args) in (tuple, list): 
        raise TypeError, "execv() arg 2 must be a tuple or list" 
    path = os.path.abspath(path) 
    args = " ".join(_quote(arg) for arg in args) 
    _create_process(path, args) 
    
def execve(path, args, env): 
    execv(path, args) 
    
def systema(path, args): 
    if not type(args) in (tuple, list): 
        raise TypeError, "systema() arg 2 must be a tuple or list" 
    path = os.path.abspath(path) 
    args = " ".join(_quote(arg) for arg in args) 
    
    hPro = _create_process(path, args)
    
    # Don't wait, just return
    return 
    return _wait_process(hPro)