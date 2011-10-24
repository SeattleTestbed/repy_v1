/*****************************************************************
<File Name>
  tr_repy.js

<Started>
  March, 2011

<Author>
  lukas.puehringer@univie.ac.at
  Lukas Puehringer

<Purpose>
  This is the the only non-ace java script file in Try Repy.
  It initializes the ace editor.
  It reloads ace themes, to accelerate first loading.
  It provides ajax transmission to request the log, submit the code and 
  receive the output.
  Additionally it controls the navigiation menu (toggle_bar) and provides
  possibility to insert files to the editor. 

*****************************************************************/


var g_editor;
var g_canon;
var g_submit_button;
var g_xmlHttp_log = false;
var g_xmlHttp_evaluate = false;
var g_xmlHttp_outputbuffer = false;

function init_ace() {
  /*****************************************************************
    <Purpose>
      Initializes the ace editor.
      Sets the theme to "textmate" and links (loads) other themes for
      user customization.
      Sets the SyntaxHighlighting to Python.
      
      Makes special "insert_elements" (special characters, code snippets)
      clickable and insertable.
      
      Registers key command to submit code.
      
  *****************************************************************/
  g_editor = ace.edit("editor");
  
  /* Set initial theme and load other themes */
  g_editor.setTheme("ace/theme/textmate");
  load_themes();
  
  /* Syntaxhighlighting */
  var PythonMode = require("ace/mode/python").Mode;
  g_editor.getSession().setMode(new PythonMode());
    
  g_editor.renderer.setHScrollBarAlwaysVisible(false);
  g_editor.setShowPrintMargin(false);
    
  /* Adds onClick insert to editor function 
     to all elements of class insert_element */
  make_clickable("g_editor.insert(this.innerHTML)", "insert_element");
  
  /* Stores submit code button to disable later during code evaluation. */
  g_submit_button = document.getElementById("submit_button");
  
  g_canon = require("pilot/canon");
  register_submit_key();
}


function load_themes() {
  /*****************************************************************
    <Purpose>
      In order to accelerate initial site loading, themes are loaded
      dynamically after the site is already visible/useable.
  
  *****************************************************************/
  themelist = ["clouds_midnight", "clouds", "cobalt", "crimson_editor",
    "dawn", "eclipse", "idle_fingers", "kr_theme", "merbivore_soft","merbivore",
    "mono_industrial", "monokai", "pastel_on_dark", "solarized_dark",
    "solarized_light", "twilight", "vibrant_ink" ];
    
  for (var i in themelist) {
    var js = document.createElement('script');
    js.setAttribute("charset", "utf-8", 1);
    js.setAttribute("type","text/javascript", 1);
    js.setAttribute("src", "js/ace/theme-" + themelist[i] + ".js", 1);
    document.getElementsByTagName('head')[0].appendChild(js);
  }
}


function register_submit_key() {
  /*****************************************************************
    <Purpose>
      Registers a key command for code submission.
      Enables the code submit button.
      Sets editor readonly false. 
      
  *****************************************************************/
  g_canon.addCommand({
    name: "submitCodeKey",
    bindKey: {win: "Ctrl-Return", mac: "Command-Return", sender: "editor"},
    exec: function(env, args, request) {
      deregister_submit_key();
      call_server_evaluate(env, args, request);
      toggle("output_toggle", "output_container");
    }
  }); 
  
  g_submit_button.disabled = false;
  g_editor.setReadOnly(false);
  
}



function deregister_submit_key() {
  /*****************************************************************
    <Purpose>
      Deregisters a key command for code submission. Sets editor 
      readonly true. This is done while submitted code is evaluated, 
      to prohibit another interfering code submission.
      
  *****************************************************************/
  g_submit_button.disabled = true;
  g_editor.setReadOnly(true);
  g_canon.removeCommand('submitCodeKey');
}



function create_xml_http() {
  /*****************************************************************
    <Purpose>
      Creates an XmlHttp (ajax) object.
    
    <Returns>
      XmlHttp object (java script object)
  *****************************************************************/  
  var xmlHttp = false;
  
  try { 
    /* try the first version of JavaScript in IE */ 
    xmlHttp = new ActiveXObject("Msxml2.XMLHTTP");
  } catch (e) {
    try {
      /* try the second version of JavaScript in IE */ 
      xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
    } catch (e2) {
      xmlHttp = false;
    }
  }

  /* else create the object the non-Microsoft way. */ 
  if (!xmlHttp && typeof XMLHttpRequest != "undefined") {
    xmlHttp = new XMLHttpRequest();
  }
  
  return xmlHttp;
}


function call_server_log() {
  /*****************************************************************
    <Purpose>
      Requests session log via ajax GET.
      Upon receiving response, response is turned into an JSON object
      for easier access and inserted to the log div. If the response is
      empty, it means the webinterface has no sandbox on the server.
      If the response is an empty JSON object, the sandbox exists, but
      nothing has been logged yet.
  
  *****************************************************************/  
  g_xmlHttp_log = create_xml_http();
  
  var url = "getLog?" + g_user_id;
  g_xmlHttp_log.open("GET", url, true);
  g_xmlHttp_log.setRequestHeader("Content-Type", 
   "application/x-www-form-urlencoded");
   
  g_xmlHttp_log.onreadystatechange = function() {
    if (this.readyState == 4) {
      
      // Convert string to JSON Object
      var response = this.responseText;
      
      
      var log_element =  document.getElementById("log");
      log_element.innerHTML = ""
      
      if (response == "{'entire_log' : [  ] }") { 
        log_element.innerHTML = "<pre>(nothing logged yet)</pre>";
      }
      else if (response == "") {
        log_element.innerHTML =
        "<pre>You currently have no sandbox. Reload website!</pre>";
      } 
      else {
        var responseJson = eval ("(" + response + ")");

        for (var j = 0; j < responseJson.entire_log.length; j++ ) {
          log_element.innerHTML += "-----------------------------------<br/>"
          log_element.innerHTML += "Logtime: ";
          log_element.innerHTML += "<pre>" + 
            responseJson.entire_log[j].logtime + "</pre>";
          log_element.innerHTML += "Repycode: ";
          log_element.innerHTML += "<pre>"
            + htmlEntities(unescape(responseJson.entire_log[j].repycode) )
            + "</pre>";
          log_element.innerHTML += "Output: ";
          log_element.innerHTML += "<pre>"
            + htmlEntities(unescape(responseJson.entire_log[j].output) )
            + "</pre>";
          
        }
      } 
    }
  }
  g_xmlHttp_log.send(null);
}

function htmlEntities(str) {
  /*****************************************************************
    <Purpose>
      Converts characters to HTML Entities.
      
  *****************************************************************/  
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}


function call_server_evaluate(env, args, request) {
  /*****************************************************************
    <Purpose>
     Posts submitted code + call arguments via ajax. Response will be
     the evaluated codes ouput.
     Additionally it calls call_server_output.
     Upon receiving the response, it posts the repsonse to the output 
     element.

  *****************************************************************/
  g_xmlHttp_evaluate = create_xml_http();
  
  var code = g_editor.getSession().getValue();
  var user_callargs = document.getElementById("user_callargs").value;
  var input = "user_code=" + escape(code) +"&user_callargs=" + 
   escape(user_callargs);

  /* Make a connection to the server  */
  g_xmlHttp_evaluate.open("POST", "/?" + g_user_id, true);
  g_xmlHttp_evaluate.setRequestHeader("Content-Type", 
    "application/x-www-form-urlencoded");
  
  var output = document.getElementById("output");
  output.innerHTML = "";

  /* Setup a function for the server to run when it's done*/
  g_xmlHttp_evaluate.onreadystatechange = function() {   
    if (this.readyState == 4) {
      var response = this.responseText;
      output.innerHTML += htmlEntities(unescape(response));
      register_submit_key();
    }
  }
  
  // Send the request 
  g_xmlHttp_evaluate.send(input);
  call_server_buffer();
  
}

function call_server_buffer() {
  /*****************************************************************
    <Purpose>
     Calls the server for the current outputbuffer recursively until
     the xmlHttp object in call_server_evaluate has received a response.

  *****************************************************************/
  g_xmlHttp_outputbuffer = create_xml_http();

  var url = "getOutput?" + g_user_id;
  g_xmlHttp_outputbuffer.open("GET", url, true);
  g_xmlHttp_outputbuffer.setRequestHeader("Content-Type", 
   "application/x-www-form-urlencoded");
   
  var output = document.getElementById("output");
   
  g_xmlHttp_outputbuffer.onreadystatechange = function() {
    if (this.readyState == 4) {
      
      var response = this.responseText;
      output.innerHTML += htmlEntities(unescape(response));

      if (g_xmlHttp_evaluate.readyState != 4) {
        call_server_buffer();
      }
    }
  }
  g_xmlHttp_outputbuffer.send(null);

}

function make_clickable(function_str, class_name) {
  /*****************************************************************
    <Purpose>
     Assigns OnClick function <function_str> to an HTML element with 
     class attribute <class_name>. 
  
    <Arguments>
      function_str (string)
        A string, containing the function + arguments (how it is called).
      class_name (string)
        The class name of the element, the function should be assigned to.

  *****************************************************************/
  var elements = document.getElementsByClassName(class_name);
  for (var i = 0; i < elements.length; i++) {
    elements[i].setAttribute('onClick', function_str, 1);
   }
}


function toggle(click_class_name, toggle_class_name) {
  /*****************************************************************
    <Purpose>
     Toggles various right_box contents.
     Changes style of navigation bar.
  
    <Arguments>
      click_class (string)
        The class name of the navigation (clicked) element.
      toggle_class (string)
        The class name of the element which should be toggled.

  *****************************************************************/
  
  var click_element = document.getElementById(click_class_name);
  var click_elements = document.getElementsByClassName("click_element");
  for (var i = 0; i < click_elements.length; i++) {
    click_elements[i].style.color = "black";
    click_elements[i].style.background = "white";
   }
  click_element.style.color = "white";
  click_element.style.background = "black";
  
  var toggle_element = document.getElementById(toggle_class_name);
  var toggle_elements = document.getElementsByClassName("toggle_element");
  for (var i = 0; i < toggle_elements.length; i++) {
    toggle_elements[i].style.display = "none";
   }
  toggle_element.style.display = "";
}


function remove_file_input_row() {
  /*****************************************************************
    <Purpose>
      Removes the last input file row in Try Repy's insert file section.

  *****************************************************************/
    
  var table_element = document.getElementById("file_input_table");
  var tr_count = document.getElementsByName("file_input").length;
  var tr_element = document.getElementById(("input_row" + tr_count));
  
  table_element.removeChild(tr_element);
}


function append_file_input_row() {
  /*****************************************************************
    <Purpose>
      Appends input file row in Try Repy's insert file section.

  *****************************************************************/
  
  var table_element = document.getElementById("file_input_table");
  var tr_count = document.getElementsByName("file_input").length;

  var tr_element = document.createElement("tr");
  tr_element.id = "input_row" + (tr_count + 1);
  
  var td_element = document.createElement("td");
  
  var file_element = document.createElement("input");
  file_element.type = "file";
  file_element.name = "file_input";
  file_element.accept = "text/*";
  
  td_element.appendChild(file_element);
  tr_element.appendChild(td_element);
  table_element.appendChild(tr_element);
}


function process_file_form() {
  /*****************************************************************
    <Purpose>
      Reads in input elements from HTML Form Data in order to insert
      locally stored files to the editor window. 

  *****************************************************************/
  
  var insert_mode;
  var insert_mode_len = document.file_form.file_insert_mode.length;
  
  for (i = 0; i < insert_mode_len; i++) {
    if ( document.file_form.file_insert_mode[i].checked ) {
      insert_mode = document.file_form.file_insert_mode[i].value;
      break;
    }
  }
  
  var delim_mode;
  var delim_mode_len = document.file_form.file_delim_mode.length;
  
  for (j = 0; j < delim_mode_len; j++) {
    if ( document.file_form.file_delim_mode[j].checked ) {
      delim_mode = document.file_form.file_delim_mode[j].value;
      break;
    }
  }
  
  var files = document.getElementsByName("file_input");
  var files_len = document.getElementsByName("file_input").length;
  
  for (k = 0; k < files_len; k++) {
    file = files[k].files[0];
    read_file(file, insert_mode, delim_mode);
  }
  
}


function read_file(file, insert_mode, delim_mode) {
  /*****************************************************************
    <Purpose>
      Helper function that creates a FileReader for the passed 
      file_object. It reads the data and creates a callback function
      for when the file is read. 
      
    <Arguments>
      file
        HTML [file object]
        
      insert_mode  (string) 
        "begin" or "cursor" - specifies where exactly in the editor window the
        file should be inserted
      
      delim_mode (string)
        "lines", "line" or "none" - specifies what delimter should be used
        
  *****************************************************************/
  
	var file_reader;
	try {
    file_reader = new FileReader();
	} catch(e) {
		alert("Error: seems File API is not supported on your browser");
  }

  file_reader.onload = function(e) { 
    insert_file(file.fileName, e.target.result, insert_mode, delim_mode) 
  }
  
  file_reader.readAsText(file, "UTF-8");
}

function insert_file(file_name, content, insert_mode, delim_mode) {
  /*****************************************************************
    <Purpose>
      Callbackfunction when a file to be inserted is read. 
      It specifies the delimiter, and the place where the file should
      be inserted. 
      
    <Arguments>
      file_name (string)
      
      content (string)
      
      insert_mode  (string) 
        "begin" or "cursor" - specifies where the file should be inserted
      
      delim_mode (string)
        "lines", "line" or "none" - specifies what delimter should be used
        
    <Side Effects>
      None.
    <Returns>
      None.
  *****************************************************************/


  // Make Delimiter.
  var delimiter_top = "\n\n";
  var delimiter_bottom = "\n\n";
  
  if (delim_mode == "lines") {
    delimiter_top += 
     "#######################################################\n" + 
     "#######################################################\n" + 
     "#######################################################\n" + 
     "#######################################################\n" + 
     "# begin include '" + file_name + "'\n";
  
    delimiter_bottom += 
     "# end include " + file_name + "'\n\n";
  
  } else if (delim_mode == "line") {
      delimiter_top += 
       "# begin include '" + file_name + "'\n";
  
      delimiter_bottom += 
       "# end include " + file_name + "'\n\n";
    }
  
  
  if (delim_mode == "begin") {
    g_editor.gotoLine(0);
  }

  g_editor.insert(delimiter_top + content + delimiter_bottom);
  
}
