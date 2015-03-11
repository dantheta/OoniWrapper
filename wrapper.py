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

from amqplib import client_0_8 as amqp

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

if cfg.has_section('api'):
	for k,v in cfg.items('api'):
		if k == 'https':
			setattr(APIRequest,k.upper(),v.lower()=='true')
		else:
			setattr(APIRequest,k.upper(),v)
	
signer = RequestSigner(cfg.get('probe','secret'))

ENV = {k.upper():v for (k,v) in cfg.items('environment')}
logging.info("Environment: %s", ENV)

args = []
if cfg.has_option('probe','public_ip'):
	args.append( cfg.get('probe','public_ip'))

req = StatusIPRequest(signer, *args, probe_uuid=cfg.get('probe','uuid'))
ret, ip = req.execute()
logging.info("Return: %s", ip)
queue = 'url.' + (ip['isp'].lower().replace(' ','_')) + '.' + cfg.get('probe','queue')


amqpopts = dict(cfg.items('amqp'))

logging.info("Opening AMQP connection")
conn = amqp.Connection(**amqpopts)
ch = conn.channel()
urls = []


def write(urls):
	fp = tempfile.NamedTemporaryFile()
	for url in urls:
		print >>fp, url
	fp.flush()
	return fp

def run(tmpfp):
	with open(cfg.get('global','template')) as fp:
		data = yaml.load(fp)
	for test in data:
		test['options']['subargs'][1] = tmpfp.name

	deckfp = tempfile.NamedTemporaryFile()
	deckfp.write(yaml.dump(data))
	deckfp.flush()
	
	env = ENV.copy()
	env['PROBE_ID'] = cfg.get('probe','uuid')
	env['PROBE_AUTH'] = signer.sign(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'))
		
	st = time.time()
	proc = subprocess.Popen(
		[cfg.get('global','oonipath'),'-i',deckfp.name],
		env=env
		)
	ret = proc.wait()
	logging.info("Test complete: duration %s", time.time() - st)
	tmpfp.close()
	deckfp.close()

def consume(msg):
	"""Direct execution"""
	data = json.loads(msg.body)
	logging.info("Got url: %s", data['url'])
	ch.basic_ack(msg.delivery_tag)
	
	fp = write([data['url']])
	run(fp)

def consume2(msg):
	"""Gather URLs"""
	data = json.loads(msg.body)
	logging.info("Got url: %s", data['url'])
	ch.basic_ack(msg.delivery_tag)
	
	urls.append(data['url'])
	signal.alarm(0)
	signal.alarm(int(cfg.get('global','interval')))

logging.info("Listening on queue: %s", queue)
ch.basic_qos(0,cfg.getint('probe','qos'),False)
ch.basic_consume(queue, consumer_tag='consumer1',callback=consume2)
while True:
	signal.alarm(int(cfg.get('global','interval')))
	def stop(*args):
		logging.debug("Timeout")
	signal.signal(signal.SIGALRM,stop)
	while True:
		try:
			ch.wait()
		except socket.error:
			break
	if urls:
		logging.info("Got urls: %s", urls)
		fp = write(urls)
		run(fp)
		del urls[:]

conn.close()


