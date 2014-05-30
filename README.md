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

Running
=======

When running, the script will pull [global.fetch] URLs from the API, write them to a temporary file and then launch ooniprobe.

The command line for running ooniprobe is built from the [global.ooniprobe] and [global.args] settings.  Ooniwrapper automatically appends "-f <temporary_filename>" to the command when running.  After an ooniprobe run has completed, the program sleeps for [global.interval] seconds.
