
import sys
import json
import hmac
import logging
import hashlib
import datetime
import requests

__all__ = ['RegisterProbeRequest','PrepareProbeRequest','StatusIPRequest','RequestHttptRequest','APIRequest']

class APIRequest(object):
	HTTPS=True
	HOST = 'api.blocked.org.uk'
	PORT = 80
	VERSION='1.2'
	SEND_TIMESTAMP=True
	SIG_KEYS = []
	ENDPOINT = None
	METHOD = 'POST'

	def __init__(self, secret, *urlargs, **kw):
		self.args = kw
		self.urlargs = urlargs
		self.secret = secret

	def get_url(self):
		urlargs = '/'.join(self.urlargs)
		return "{}://{}:{}/{}/{}{}{}".format(
			'https' if self.HTTPS else 'http',
			self.HOST,
			self.PORT,
			self.VERSION,
			self.ENDPOINT,
			'/' if urlargs else '',
			urlargs)

	def timestamp(self):
		return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	def sign(self, *args):
		msg = ':'.join([str(x) for x in args])
		logging.debug("Using signature string: %s", msg)
		hm = hmac.new(self.secret, msg, hashlib.sha512)
		return hm.hexdigest()

	def get_signature(self):
		return self.sign(*[self.args[x] for x in self.SIG_KEYS])

	def execute(self):
		if self.SEND_TIMESTAMP:
			self.args['date'] = self.timestamp()
		self.args['signature'] = self.get_signature()
		logging.info("Sending args: %s", self.args)
		if self.METHOD == 'GET':
			rq = requests.get(self.get_url(), params=self.args)
		else:
			rq = requests.post(self.get_url(), data=self.args)

		try:
			return rq.status_code, rq.json()
		except ValueError:
			print >>sys.stderr, rq.content

class PrepareProbeRequest(APIRequest):
	ENDPOINT = 'prepare/probe'
	SIG_KEYS = ['email','date']

class RegisterProbeRequest(APIRequest):
	ENDPOINT = 'register/probe'
	SEND_TIMESTAMP=False
	SIG_KEYS = ['probe_uuid']
	
class StatusIPRequest(APIRequest):
	ENDPOINT = 'status/ip'
	SIG_KEYS = ['date']
	METHOD = 'GET'

class RequestHttptRequest(APIRequest):
	ENDPOINT = 'request/httpt'
	SIG_KEYS = ['probe_uuid']
	METHOD = 'GET'
	SEND_TIMESTAMP=False

