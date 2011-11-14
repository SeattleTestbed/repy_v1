TRY REPY

Try Repy is a web-based software development and execution environment for Repy, which was implemented in the course of a bachelor seminar in the year 2011 at the research group of Future Communication at the University of Vienna.

############
Author

Lukas Puehringer
lukas.puehringer@univie.ac.at


############
Installation

- Make sure, the file restrictions.tryrepy contains the serverport:
resource connport <serverport>

- run inside this directory
./tr_build.sh
./tr_run.sh </abspath/to/seattle_repy> <serverport>


############
Known Issues

- Print does not work, use log() instead.
- Infinity Loops can only be stopped by shutting down the entire server
- Exitall() does not work
- Thread Exceptions:
A thread exception in one thread does not exit the entire evaluation in a Virutal Namespace.  So far exceptions in a thread are caught and logged but the execution of other healthy threads continues.
- TCP/UDP listeners are not isolated
A listener registered on one IP:PORT will override another listener previously registered on this IP:PORT 
 
############   
Links

https://seattle.cs.washington.edu/wiki
https://seattle.cs.washington.edu/wiki/ProgrammersPage
https://seattle.cs.washington.edu/wiki/RepyApi

############   
Description

- Editor
The editor is always displayed on the left side. You can write Repy code to it  and evaluate it on the server. To submit the code press cmd + return (mac), ctrl + return (win), or the submit button beneath the editor window. Until the code has been evaluated, codesubmission is locked.
  
- Callargs
You can append space separated callarguments in the input line beneath the  editor window, when submitting code.
  
- Standard Output
This displays the output of the program. It gives "real time" feedback.

- Session Log
This retrieves and displays the entire log for every submitted and evaluated code of a session

- Insert Files
Insert files to the editor window, whether at cursor position or at the top of the editor window. 

- Special Characters
Insert special characters at cursor position.

- Code Snippets
Insert code snippets at cursor position.

- Editor Options
Options to customize the editor window.

- Read Me
this.
  
Todo

- Network Ressource scheduling
- Isolation of UDP and TCP listener
- Repy Preprocessing
- Thread Exceptions should stop entire program
