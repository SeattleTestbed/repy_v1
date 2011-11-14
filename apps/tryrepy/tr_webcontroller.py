"""
<Program Name>
  tr_webcontroller.repy

<Started>
  March, 2011

<Author>
  Lukas Puehringer, University of Vienna
  lukas.puehringer@univie.ac.at

<Purpose>
  This component is the dispatcher for the Try Repy webinterface. It
  handels HTTP requests from the webfronted, does user handling and
  instantiates per user sandboxes.
  
  Requests can be:
  HTTP Filerequests
    responds with HTML, CSS, JS files
  Ajax POST Requests
    receives posted code, evaluates it in the user's sandbox
  Ajax GET Requests
    responds with users sandbox log or current output buffer.

"""


######
# Global Imports: Everybody needs these libraries
include base64.repy
include tr_fileabstraction.repy 
include tr_sandbox.repy 

######
# Copy the current context before including libraries the user does
# not need.

mycontext["clean_user_context"] = _context.copy()

######
# Other Imports: Only the webcontroller should access these libraries

include httpserver.repy
include urllib.repy
include random.repy


def read_and_decode_form_data(datastream):
  """
  <Purpose>
    Reads the url-encoded Ajax posted Repy code + optional 
    callarguments and decodes it.
  
  <Arguments>
    datastream (string)
      Url-encoded HTTP datastream.
      
  <Returns>
    data_dictionary (dict)
      contains entries for callarguments and code. 
  """

  data_urlencoded = ""
  while True:
    new_chunk = datastream.read(4096)
    data_urlencoded += new_chunk
    if len(new_chunk) == 0:
      break
  
  # Actually this is the urllib_unquote_parameters method,
  # but unlike the original one, mine does not call urllib_unquote_plus.
  
  keyvalpairs = data_urlencoded.split("&")
  data_dict = {}
  
  for quotedkeyval in keyvalpairs:
    # Throw ValueError if there is more or less than one "=".
    quotedkey, quotedval = quotedkeyval.split("=")
    key = urllib_unquote(quotedkey)
    val = urllib_unquote(quotedval)
    val = val.strip()
    if key == "user_callargs":
      val = val.split(" ")
    data_dict[key] = val 
    
  return data_dict
  
  
def exist_user(http_request_dict):
  """
  <Purpose>
    Checks if the http_request_dict contains a querystring that is 
    an existing user id, with an according sandbox.
    
  <Arguments>
    http_request_dict (dict)
    
  <Returns>
    True/False
  """
  
  if http_request_dict["querystr"] in mycontext["user_dict"].keys():
    return True
  else:
    return False


def serve_user():
  """
  <Purpose>
    Generates a random user id and instantiates a Sandbox for the user.
    It returns a JavaScript global variable, to inform the webinterface
    about its user id.

  <Returns>
    JavaScript Code (string)
  """
  
  user_id = str(random_randint(0, 2**30))
  mycontext["lock_user_dict"].acquire()
  mycontext["user_dict"][user_id] = \
    Sandbox(user_id, mycontext['clean_user_context'].copy(), getruntime())
  mycontext["lock_user_dict"].release()
    
  return "var g_user_id = " + user_id + ";"


def make_response(status, message):
  """
  <Purpose>
    Generates a http_response_dict with variable message and statuscode.
  
  <Arguments>
    status (int)
      HTTP status message.
    message (string)
      HTTP payload
      
  <Returns>
    http_response_dict (dict)
  """ 
  
  http_response_dict = {"version": "1.1", 
              "statuscode": int(status),
              "statusmsg": "OK",
              "headers": {"Server": "TryREPY"},
              "message" : message}
    
  return http_response_dict


def serve_log(user_id):
  """
  <Purpose>
    Calls the user's entire sandbox log and converts it to a JSON string.
    Since the sandbox log dict is not chronologically orderd, the
    sorting is done here. The code and the output elements in the JSON string
    are urllib_quoted.
    
  <Arguments>
    user_id (string)
      
  <Returns>
    log_string (string)
      Urllib_quoted JSON String, containing the user's entire sandbox log.
  """ 

  log_dict = {}
  log_time_list = []
  log_string = ""
  log_html = ""
  
  mycontext["lock_user_dict"].acquire()
  
  # log_dict format
  # log { "<logtime>" : { code" : "<code>", "output" : "<output>" }, .. }
  log_dict = mycontext["user_dict"][user_id].get_log()
  
  mycontext["lock_user_dict"].release()
  
  # The log_dicts keys are timestamps. The log_time_list is used to sort
  # the unorderd dictionary.
  log_time_list = log_dict.keys()
  log_time_list.sort()
  
  # Create a JSON object - this is awesome :)
  
  log_string = "{'entire_log' : [ "

  for log_time in log_time_list:
  
    log_string += "{" + \
    "'logtime':'" + str(log_time) + "', " + \
    "'repycode':'" + urllib_quote(str(log_dict[log_time]["code"]) ) + "', " + \
    "'output':'" + urllib_quote( str(log_dict[log_time]["output"]) ) + "'" + \
    "},"

  log_string += " ] }"
  
  return log_string


def serve_code(data_dict, user_id):
  """
  <Purpose>
    Passes the user posted Repy code + optional callarguments to the sandbox
    where it is evaluated. It returns the remaining part of the outputbuffer.
    
  <Arguments>
    data_dict (dict)
      A dictionary with user_code and user_callargs
    user_id
          
  <Returns>
    output (string)
      A urllib_quoted string of the remaining part of the outputbuffer.
  """ 
  
  # Calls sandbox's evaluate_repy method and receives the ouput. 
  output = mycontext["user_dict"][user_id].evaluate_repy \
    (data_dict["user_code"], data_dict["user_callargs"])
  
  return urllib_quote(output)
  
def serve_output_buffer(user_id):
  """
  <Purpose>
    Calls sandbox's read_output_buffer for the specified user.
    If the ouputbuffer is empty, it waits a second and retries 
    reading 5 times. This reduces ajax polling frequency.
    If the buffer stays empty it returns an empty string, 
    else the output_buffer's content.
    
  <Arguments>
    user_id
      
  <Returns>
    output (string)
      A urllib_quoted string of the current outputbuffer.
  """ 
  
  for count in range(0,5):
    # This could be parameterized when the webcontroller is called.
    sleep(1)
    output = mycontext["user_dict"][user_id].read_output_buffer()
    
    if output:
      return urllib_quote(output)
      
  return urllib_quote("")
  
def serve_file(virtual_path):
  """
  <Purpose>
    Reads web files (HTML, CSS, JS) form the vessel and returns it
    to the HTTP requester.
    
    It explicitly uses the tr_fileabstraction functions/methods for
    filename translation. See tr_fileabstraction for further information.
    
  <Arguments>
    virtual_path(string)
      The path of a file, how it is known to the web application.
      
  <Returns>
    content_file(string)
      
  """ 
  
  # If root is requestd, index.html is used instead.
  if virtual_path == "/":
    virtual_path = "/index.html"

  if virtual_path.startswith("/"):
    virtual_path = virtual_path.lstrip("/")
  
  # Calling functions in tr_fileabstraction.repy
  tmp_file = tr_open("system", virtual_path)
  content_file = tmp_file.read()
  tmp_file.close()
    
  return content_file

def serve(http_request_dict):
  """
  <Purpose>
    The serve dispatcher calls, checks for the type of request 
    and forwards it to the according function. It expects the message's content
    as return value.
    
    Possible requests are:
      POST request containing repy code, requesting code evaluation
      GET request with prefix "/getOutput", requesting output buffer
      GET request with prefix "/getLog", requesting sandbox log
      GET request with prefix "/js/tr_repy_user.js", requesting for new user_id
      GET request web files
      
  <Arguments>
    http_request_dict
      
  <Returns>
    http_response_dict
  """ 
  # Print the http_request_dict to the console.
  print http_request_dict
  
  # The message that will be responded.
  message = ""
  
  # Serve Code if user exists. 
  if (http_request_dict["verb"].upper() == "POST"):
    if exist_user(http_request_dict):
      data_dict = read_and_decode_form_data(http_request_dict["datastream"])
      message = serve_code(data_dict, http_request_dict['querystr'])
    else:
      message = "You currently have no sandbox. Reload website!"
    
  # Serve current output buffer if user exists
  elif (http_request_dict["verb"].upper() == "GET") and \
    http_request_dict["path"].startswith("/getOutput"):
    if exist_user(http_request_dict):
      message = serve_output_buffer(http_request_dict['querystr'])
    else:
      message = ""
    
  # Serve log if user exists
  elif (http_request_dict["verb"].upper() == "GET") and \
    http_request_dict["path"].startswith("/getLog"):
    user_id = exist_user(http_request_dict)
    if user_id:
      message = serve_log(http_request_dict['querystr'])
    else:
      message = ""
    
  # Called in index.html, instantiates new user id and returns a js variable
  elif (http_request_dict["verb"].upper() == "GET") and \
    http_request_dict["path"].startswith("/js/tr_repy_user.js"):
    message = serve_user()
  
  # This looks for the requested file in the vessel
  elif (http_request_dict["verb"].upper() == "GET"):
    message = serve_file(http_request_dict["path"])
  
  # Is this case even possible?  
  else:
    message = "Get Lost!"

  http_response_dict = make_response(200, message)
  
  return http_response_dict


if callfunc == "initialize":
  
  # These are currently the only two global variables.
  # The user_dict contains all existing sandboxes with their user_id
  # as key.
  
  try:
    port = int(callargs[0])
  except:
    print "Needs argument <port number>!"
    
  else:
    #port = 63134
    
    mycontext["user_dict"] = {}
    # The locks handles race conditions when the user_dict is accessed.
    mycontext["lock_user_dict"] = getlock()

    print "Webinterface available on:\nhttp://" + getmyip() + ":" + str(port)

    # Run the server...
    httpserver_registercallback((getmyip(), port), serve)
