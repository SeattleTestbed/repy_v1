# MapReduce for python/repy!
#

def get_data(ip, port, sockobj, thiscommhandle, listencommhandle):
    """ Listens for connections on a well-defined port, imports data files """
    
     # parse and save map.py, reduce.py, data file
    filenames = array('map.py', 'reduce.py', 'map_data.dat')
    for i in range(3):
        # get length of following data
        data_len = int(sockobj.recv(4))
        
        # parse actual data, write to file
        buf = str(sockobj.recv(data_len))
        py_file = open(filenames[i], "w")
        py_file.write(buf)
        py_file.close()
        
    # destroy the listen socket as we're done initializing
    mycontext['state'] = 'Initialized'
    stopcomm(listencommhandle)
    
# Assumptions to make this simpler:
# - all this data fits in memory (<2 GB) in the variable map_result
# - data is stored in the files/string as "(key)(\t)(value)"  
def map():
    from map import *
    
    data = open("map_data.dat", "r")
    
    map_result = []
    for line in data:
        line_parts = line.partition('\t')
        # I assume that results are returned in the form "<key>\t<value>"
        # map.mapper takes key, value as two separate arguments
        map_result.append(map.mapper(line_parts[0], line_parts[2]))
                          
    return map_result.sort(key=str.lower())
    
    
# one artificial restriction here is that the key must start with A-Z or a-z.
# case is sensitive as in Hadoop
def partition(map_result):
    len_partition = 52 / mycontext["num_reducers"]
    len_partition_remainder = 52 % mycontext["num_reducers"]
    
    firstLetter = 65
    difference = 26+7
    
    #foreach result in map_result:
    pass
    
    
def reduce():
    from reduce import *
    
    data = open("reduce_data.dat", "r")
    
    reduce_result = []
    for line in data:
        line_parts = line.partition('\t')
        # I assume that results are returned in the form "<key>\t<value>"
        # reduce.reducer takes key, value as two separate arguments
        reduce_result.append(reduce.reducer(line_parts[0], line_parts[2]))
                          
    return reduce_result.sort()

# TODO...
def report_results(map_results):
    pass
    
    
if callfunc == 'initialize':
    mycontext['num_mappers'] = 1
    mycontext['num_reducers'] = 1
    mycontext['state'] = 'Ready'
    
    if len(callargs) > 1:
        raise Exception("too many args")
    
    elif len(callargs) == 1:
        port = int(callargs[0])
        ip = getmyip()
    
    else:
        port = 12345
        ip = '127.0.0.1'
    
    listencommhandle = waitforconn(ip, port, get_data)
    
    # block until we've been initialized with data/methods
    while mycontext['state'] == 'Ready':
        sleep(5)
    
    # start mapping, synchronous call
    map_result = map()

    # send map results to all reducers, split as necessary
    partition(map_result)
    
    while mycontext['state'] == 'ReducerWaiting':
        sleep(5)
        
    # start reducing, synchronous call (wait for all data to come in, then start)
    reduce_result = reduce()
    
    report_results(reduce_result)
