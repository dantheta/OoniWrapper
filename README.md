OoniWrapper
===========

Wrapper script for ooniprobe that pulls test URLs from the ORG blocked.org.uk API


Requirements:

 * python requests library


Before running, create the file ooniwrapper.ini (example included).  Place the ORG probe key credentials (uuid & secret) 
in a section of the ini file.

To run:

$ python wrapper.py

Optional Configuration
----------------------

override_network: In cases where the server-side detection of the client's ISP fails, override_network can be used to hard-code
a network operator name for the probe.  The configuration item should match the value of queue_name on the server's record for the ISP.


