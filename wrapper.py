#!/usr/bin/env python

import os
import sys
import json
import time
import yaml
import getopt
import signal
import socket
import logging
import datetime
import tempfile
import subprocess
import ConfigParser

from signing import RequestSigner
from api import StatusIPRequest,APIRequest


optargs, optlist = getopt.getopt(sys.argv[1:],'vc:')
opts = dict(optargs)

logging.basicConfig(
	level=logging.DEBUG if '-v' in opts else logging.INFO,
	datefmt="[%Y-%m-%d %H:%M:%S]",
	format="%(asctime)s\t%(levelname)s\t%(message)s"
)

cfg = ConfigParser.ConfigParser()
read = cfg.read([opts['-c']] if '-c' in opts else ['wrapper.ini'])
assert len(read) > 0
signer = RequestSigner(cfg.get('probe','secret'))

if cfg.has_section('api'):
	for k,v in cfg.items('api'):
		if k in ('https','verify'):
			setattr(APIRequest,k.upper(),v.lower()=='true')
		else:
			setattr(APIRequest,k.upper(),v)
	

ENV = {k.upper():v for (k,v) in cfg.items('environment')}
logging.info("Environment: %s", ENV)
ENV['PROBE_UUID'] = cfg.get('probe','uuid')
ENV['PROBE_AUTH'] = signer.sign(cfg.get('probe','uuid'))

args = []
if cfg.has_option('probe','public_ip'):
	logging.warn("Using hard-coded IP: %s",  cfg.get('probe','public_ip'))
	args.append( cfg.get('probe','public_ip'))

# while True:
if True:

	# get network name and queue
	req = StatusIPRequest(signer, *args, probe_uuid=cfg.get('probe','uuid'))
	ret, ip = req.execute()
	logging.info("Return: %s", ip)
	queue = 'url.' + (ip['isp'].lower().replace(' ','_')) + '.' + cfg.get('probe','queue')

	amqp_url = "amqp://{Q[userid]}:{Q[password]}@{Q[host]}:{Q[port]}{Q[vhost]}/{queue}".format(
		Q = dict(cfg.items('amqp')),
		queue=queue
		)
	logging.info("AMQP Url: %s", amqp_url)
		
	proc = subprocess.Popen(
		[cfg.get('global','oonipath'),'-Q',amqp_url, cfg.get('global','nettest')],
		env=ENV
		)

	def on_signal(sig,stack):
		logging.info("Wrapper received signal: %s", sig)
		proc.send_signal(signal.SIGINT)
	signal.signal(signal.SIGTERM, on_signal)
	signal.signal(signal.SIGINT, on_signal)
		
	ret = proc.wait()
	logging.info("Process ended: %s", ret)


