import requests
import jwt
from datetime import datetime, timedelta
import time

ALGORITHM = 'ES256'
BASE_API = "https://api.appstoreconnect.apple.com"


class Api:

	def __init__(self, key_id, key_file, issuer_id):
		self._token = None
		self.token_gen_date = None
		self.exp = None
		self.key_id = key_id
		self.key_file = key_file
		self.issuer_id = issuer_id
		token = self.token  # generate first token

	def _generate_token(self):
		key = open(self.key_file, 'r').read()
		self.token_gen_date = datetime.now()
		exp = int(time.mktime((self.token_gen_date + timedelta(minutes=20)).timetuple()))
		return jwt.encode({'iss': self.issuer_id, 'exp': exp, 'aud': 'appstoreconnect-v1'}, key,
		                   headers={'kid': self.key_id, 'typ': 'JWT'}, algorithm=ALGORITHM).decode('ascii')

	def _api_call(self, route):
		headers = {"Authorization": "Bearer %s" % self.token}
		url = "%s%s" % (BASE_API, route)
		r = requests.get(url, headers=headers)
		if r.status_code == 200:
			return r.json()
		else:
			print("Error [%d][%s]" % (r.status_code, r.content))
			return r

	def apps(self):
		return self._api_call("/v1/apps")

	def users(self):
		return self._api_call("/v1/users")

	def user_invitations(self):
		return self._api_call("/v1/userInvitations")

	def beta_groups(self):
		return self._api_call("/v1/betaGroups")

	def beta_testers(self):
		return self._api_call("/v1/betaTesters")

	def builds(self):
		return self._api_call("/v1/builds")

	@property
	def token(self):
		# generate a new token every 15 minutes
		if not self._token or self.token_gen_date + timedelta(minutes=15) > datetime.now():
			self._token = self._generate_token()

		return self._token