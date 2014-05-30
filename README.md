OoniWrapper
===========

Wrapper script for ooniprobe that pulls test URLs from the ORG blocked.org.uk API


Requirements:

 * python requests library


Before running, create the file ooniwrapper.ini (example included).  Place the ORG probe key credentials (uuid & secret) 
in a section of the ini file.

To run:

$ python wrapper.py

There is a basic registration function that can be invoked:

$ python wrapper.py --register --email <myemail@example.com> --secret <user secret>

This will run the prepare/probe and register/probe steps, and save the configuration to ooniwrapper.ini.

