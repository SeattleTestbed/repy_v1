# MapReduce for python/repy!
#
#
# TODO list:
#
#

import socket

def main(self):
    numMappers = 1;
    numReducers = 1;
    
    get_data(8349, 1)
    map(numReducers)
    reduce()
    

def get_data(self, port, numMappers):
    """ Listens for connections on a well-defined port, imports data files """
    
    # set up socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), port))
    s.listen(1)
   
    #accept connections from outside
    (clientsocket, address) = serversocket.accept()
    
    # parse and save map.py, reduce.py, data file
    filenames = array('map.py', 'reduce.py', 'map_data.dat')
    for i in range(3):
        # parse length info
        buf = ''
        while len(buf) < 4:
            chunk = clientsocket.recv(4)
            if chunk == '':
                raise RuntimeError, "socket connection broken prematurely"
            buf = buf + chunk
        data_len = int(buf)
        
        # parse actual data, write to file
        buf = ''
        while len(buf) < data_len:
            chunk = clientsocket.recv(data_len-len(buf))
            if chunk == '':
                raise RuntimeError, "socket connection broken prematurely"
            buf = buf + chunk
        
        py_file = open(filenames[i], "w")
        py_file.write(buf)
        py_file.close()
    
# Assumptions to make this simpler:
# - all this data fits in memory (<2 GB) in the variable map_result
# - data is stored in the files/string as "(key)(\t)(value)"  
def map():
    from map import *
    
    data = open("map_data.dat", "r")
    
    map_result = []
    for line in data
        map_result.append(map.mapper(line))
    map_result.sort();
    
    
def reduce():
    from reduce import *
    reduce.reducer()
