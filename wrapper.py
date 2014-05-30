
import os
import sys
import time
import getopt
import ConfigParser
import requests
import logging
import hashlib
import tempfile

import subprocess

from api import *


def register(opts, config):
	req = PrepareProbeRequest(opts['--secret'], email=opts['--email'])
	code, data = req.execute()

	print code, data

	if data['success'] is not True:
		logging.error("Unable to prepare probe: %s", data)
		return

	probe_uuid = hashlib.md5(opts['--seed']+'-'+data['probe_hmac']).hexdigest()
	req2 = RegisterProbeRequest(opts['--secret'], email=opts['--email'],
		probe_seed=opts['--seed'],
		probe_uuid=probe_uuid,
		type='raspi',
		)
	code2,data2 = req2.execute()
	print code2,data2

	if data2['success'] is not True:
		logging.error("Unable to prepare probe: %s", data2)
		return

	config.add_section(opts['--seed'])
	config.set(opts['--seed'], 'uuid', probe_uuid)
	config.set(opts['--seed'], 'secret', data2['secret'])
	

def run(args, opts, config):
	if len(args) > 0:
		probename = args[0]
	else:
		probename = [x for x in config.sections() if x not in ('api','global')][0]

	logging.info("Using probe: %s", probename)

	probe = {x: config.get(probename,x) for x in config.options(probename)}

	req = StatusIPRequest(probe['secret'], probe_uuid=probe['uuid'] )
	code, data = req.execute()

	logging.info("Status: %s, %s", code, data)
	if data['success'] != True:
		logging.warn("Unable to get status: %s", data['error'])
		return 1

	isp = data['isp']

	while True:
		rq = RequestHttptRequest(probe['secret'], 
			probe_uuid=probe['uuid'], 
			batchsize=config.getint('global','fetch'),
			network_name=isp
			)
		code, data = rq.execute()
		if code == 404:
			time.sleep(config.getint('global','interval'))
			continue

		if code != 200:
			logging.error("Error getting URLs: %s", data)
			return

		fp = tempfile.NamedTemporaryFile(delete=False)
		for url in data['urls']:
			print >>fp, url['url']
		fp.close()

		# do stuff
		try:
			proc = subprocess.Popen(
				[config.get('global','ooniprobe')] + 
				config.get('global','args').split(' ') + 
				['-f', fp.name])
			proc.wait()
		except OSError:
			logging.error("Unable to launch OONI")
			return

		finally:
			#os.unlink(fp.name)
			pass

		time.sleep(config.getint('global','interval'))



		
	

def main():
	optlist, optargs = getopt.getopt(sys.argv[1:],
		'c:v',
		['register','email=','secret=','seed=']
		)
	opts = dict(optlist)
	logging.basicConfig(
		level = logging.DEBUG if '-v' in opts else logging.INFO,
		datefmt = '[%Y-%m-%d %H:%M:%S]',
		format='%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s')

	configfile = opts.get('-c','ooniwrapper.ini')
	config = ConfigParser.ConfigParser()
	loaded = config.read([configfile])
	logging.info("Loaded %s config files from %s", loaded, configfile)

	if not config.has_section('global'):
		config.add_section('global')
		config.set('global','fetch',100)
		config.set('global','interval',90)
		config.set('global','ooniprobe','ooniprobe')
		config.set('global','args','')
		with open(configfile,'w') as fp:
			config.write(fp)

	if config.has_section('api'):
		for (key, value) in config.items('api'):
			logging.debug("Setting API %s = %s", key, value)
			if key == 'https':
				APIRequest.HTTPS = (value == 'True')
			else:
				setattr(APIRequest, key.upper(), value)


	if '--register' in opts:
		register(opts, config)
		with open(configfile,'w') as fp:
			config.write(fp)
		sys.exit(0)

	else:
		logging.info("Entering run mode")
		run(optargs, opts, config)
		sys.exit(0)

if __name__ == '__main__':
	main()
