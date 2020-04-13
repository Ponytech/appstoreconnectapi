import requests
import jwt
import gzip
from pathlib import Path
from datetime import datetime, timedelta
import time
import json
from enum import Enum

from .resources import *

ALGORITHM = 'ES256'
BASE_API = "https://api.appstoreconnect.apple.com"


class HttpMethod(Enum):
	GET = 1
	POST = 2
	PATCH = 3


class APIError(Exception):
	pass


class Api:

	def __init__(self, key_id, key_file, issuer_id):
		self._token = None
		self.token_gen_date = None
		self.exp = None
		self.key_id = key_id
		self.key_file = key_file
		self.issuer_id = issuer_id
		self._debug = False
		token = self.token  # generate first token

	def _generate_token(self):
		try:
			key = open(self.key_file, 'r').read()
		except IOError as e:
			key = self.key_file
		self.token_gen_date = datetime.now()
		exp = int(time.mktime((self.token_gen_date + timedelta(minutes=20)).timetuple()))
		return jwt.encode({'iss': self.issuer_id, 'exp': exp, 'aud': 'appstoreconnect-v1'}, key,
		                   headers={'kid': self.key_id, 'typ': 'JWT'}, algorithm=ALGORITHM).decode('ascii')

	def _get_resource(self, Resource, resource_id):
		url = "%s%s/%s" % (BASE_API, Resource.endpoint, resource_id)
		payload = self._api_call(url)
		return Resource(payload.get('data', {}), self)

	def _get_related_resource(self, Resource, full_url):
		payload = self._api_call(full_url)
		return Resource(payload.get('data', {}), self)

	def _get_resources(self, Resource, filters=None, sort=None, full_url=None):
		class IterResource:
			def __init__(self, api, url):
				self.api = api
				self.url = url
				self.index = 0
				self.total_length = None
				self.payload = None

			def __iter__(self):
				return self

			def __repr__(self):
				return "Iterator over %s resource" % Resource.__name__

			def __len__(self):
				if not self.payload:
					self.fetch_page()
				return self.total_length

			def __next__(self):
				if not self.payload:
					self.fetch_page()
				if self.index < len(self.payload.get('data', [])):
					data = self.payload.get('data', [])[self.index]
					self.index += 1
					return Resource(data, self.api)
				else:
					self.url = self.payload.get('links', {}).get('next', None)
					self.index = 0
					if self.url:
						self.fetch_page()
						if self.index < len(self.payload.get('data', [])):
							data = self.payload.get('data', [])[self.index]
							self.index += 1
							return Resource(data, self.api)
					raise StopIteration()

			def fetch_page(self):
				self.payload = self.api._api_call(self.url)
				self.total_length = self.payload.get('meta', {}).get('paging', {}).get('total', 0)

		url = full_url if full_url else "%s%s" % (BASE_API, Resource.endpoint)
		url = self._build_query_parameters(url, filters, sort)
		return IterResource(self, url)

	def _build_query_parameters(self, url, filters, sort = None):
		separator = '?'
		if type(filters) is dict:
			for index, (filter_name, filter_value) in enumerate(filters.items()):
				filter_name = "filter[%s]" % filter_name
				url = "%s%s%s=%s" % (url, separator, filter_name, filter_value)
				separator = '&'
		if type(sort) is str:
			url = "%s%ssort=%s" % (url, separator, sort)
		return url

	def _api_call(self, url, method=HttpMethod.GET, post_data=None):
		headers = {"Authorization": "Bearer %s" % self.token}
		if self._debug:
			print(url)
		r = {}

		if method == HttpMethod.GET:
			r = requests.get(url, headers=headers)
		elif method == HttpMethod.POST:
			headers["Content-Type"] = "application/json"
			r = requests.post(url=url, headers=headers, data=json.dumps(post_data))
		elif method == HttpMethod.PATCH:
			headers["Content-Type"] = "application/json"
			r = requests.patch(url=url, headers=headers, data=json.dumps(post_data))

		content_type = r.headers['content-type']

		if content_type in [ "application/json", "application/vnd.api+json" ]:
			payload = r.json()
			if 'errors' in payload:
				raise APIError(payload.get('errors', [])[0].get('detail', 'Unknown error'))
			return payload
		elif content_type == 'application/a-gzip':
			# TODO implement stream decompress
			data_gz = b""
			for chunk in r.iter_content(1024 * 1024):
				if chunk:
					data_gz = data_gz + chunk

			data = gzip.decompress(data_gz)
			return data.decode("utf-8")
		else:
			if not 200 <= r.status_code <= 299:
				raise APIError("HTTP error [%d][%s]" % (r.status_code, r.content))
			return r

	@property
	def token(self):
		# generate a new token every 15 minutes
		if (self._token is None) or (self.token_gen_date + timedelta(minutes=15) < datetime.now()):
			self._token = self._generate_token()

		return self._token

	# Users and Roles
	def list_users(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_users
		:return: an iterator over User resources
		"""
		return self._get_resources(User, filters, sort)

	def list_invited_users(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_invited_users
		:return: an iterator over UserInvitation resources
		"""
		return self._get_resources(UserInvitation, filters, sort)

	# TODO: implement POST requests using Resource
	def invite_user(self, all_apps_visible, email, first_name, last_name, provisioning_allowed, roles, visible_apps=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/invite_a_user
		:return: a UserInvitation resource
		"""
		post_data = {'data': {'attributes': {'allAppsVisible': all_apps_visible, 'email': email, 'firstName': first_name, 'lastName': last_name, 'provisioningAllowed': provisioning_allowed, 'roles': roles}, 'type': 'userInvitations'}}
		if visible_apps is not None:
			post_data['data']['relationships'] = {'visibleApps': list(map(lambda a: {'id': a, 'type': 'apps'}, visible_apps))}
			post_data['data']['relationships'] = {'visibleApps': visible_apps_relationship}
		payload = self._api_call(BASE_API + "/v1/userInvitations", HttpMethod.POST, post_data)
		return UserInvitation(payload.get('data'), {})

	def read_user_invitation_information(self, user_invitation_id):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/read_user_invitation_information
		:return: a UserInvitation resource
		"""
		payload = self._api_call(BASE_API + "/v1/userInvitations/" + user_invitation_id)
		return UserInvitation(payload.get('data'), {})

	# Beta Testers and Groups
	def list_beta_testers(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_testers
		:return: an iterator over BetaTester resourcwes
		"""
		return self._get_resources(BetaTester, filters, sort)

	def list_beta_groups(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_groups
		:return: an iterator over BetaGroup resources
		"""
		return self._get_resources(BetaGroup, filters, sort)

	# TODO: implement POST requests using Resource
	def create_beta_tester(self, beta_group_id, email, first_name, last_name):
		post_data = {'data': {'attributes': {'email': email, 'firstName': first_name, 'lastName': last_name}, 'relationships': {'betaGroups': {'data': [{ 'id': beta_group_id ,'type': 'betaGroups'}]}}, 'type': 'betaTesters'}}
		payload = self._api_call(BASE_API + "/v1/betaTesters", HttpMethod.POST, post_data)
		return BetaTester(payload.get('data', {}))

	def create_beta_group(self, group_name, app_id):
		post_data = {'data': {'attributes': {'name': group_name}, 'relationships': {'app': {'data': {'id': app_id, 'type': 'apps'}}}, 'type': 'betaGroups'}}
		payload = self._api_call(BASE_API + "/v1/betaGroups", HttpMethod.POST, post_data)
		return BetaGroup(payload.get('data'), {})

	def add_build_to_beta_group(self, beta_group_id, build_id):
		post_data = {'data': [{ 'id': build_id, 'type': 'builds'}]}
		payload = self._api_call(BASE_API + "/v1/betaGroups/" + beta_group_id + "/relationships/builds", HttpMethod.POST, post_data)
		return BetaGroup(payload.get('data'), {})

	# App Resources
	def read_app_information(self, app_ip):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/read_app_information
		:param app_ip:
		:return: an App resource
		"""
		return self._get_resource(App, app_ip)

	def list_apps(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_apps
		:return: an iterator over App resources
		"""
		return self._get_resources(App, filters, sort)

	def list_prerelease_versions(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_prerelease_versions
		:return: an iterator over PreReleaseVersion resources
		"""
		return self._get_resources(PreReleaseVersion, filters, sort)

	def list_beta_app_localizations(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_app_localizations
		:return: an iterator over BetaAppLocalization resources
		"""
		return self._get_resources(BetaAppLocalization, filters)

	def list_app_encryption_declarations(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_app_encryption_declarations
		:return: an iterator over AppEncryptionDeclaration resources
		"""
		return self._get_resources(AppEncryptionDeclaration, filters)

	def list_beta_license_agreements(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_license_agreements
		:return: an iterator over BetaLicenseAgreement resources
		"""
		return self._get_resources(BetaLicenseAgreement, filters)

	# Build Resources
	def list_builds(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_builds
		:return: an iterator over Build resources
		"""
		return self._get_resources(Build, filters, sort)

	# TODO: handle fields on get_resources()
	def build_processing_state(self, app_id, version):
		return self._api_call(BASE_API + "/v1/builds?filter[app]=" + app_id + "&filter[version]=" + version + "&fields[builds]=processingState")

	# TODO: implement POST requests using Resource
	def set_uses_non_encryption_exemption_setting(self, build_id, uses_non_encryption_exemption_setting):
		post_data = {'data': {'attributes': {'usesNonExemptEncryption': uses_non_encryption_exemption_setting}, 'id': build_id, 'type': 'builds'}}
		payload = self._api_call(BASE_API + "/v1/builds/" + build_id, HttpMethod.PATCH, post_data)
		return Build(payload.get('data'), {})

	def list_build_beta_details(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_build_beta_details
		:return: an iterator over BuildBetaDetail resources
		"""
		return self._get_resources(BuildBetaDetail, filters)

	# TODO: handle relationships on get_resources()
	def create_beta_build_localization(self, build_id, locale, whatsNew):
		post_data = {'data': { 'type': 'betaBuildLocalizations', 'relationships': {'build': {'data': {'id': build_id, 'type': 'builds'}}}, 'attributes': { 'locale': locale, 'whatsNew': whatsNew}}}
		payload = self._api_call(BASE_API +  "/v1/betaBuildLocalizations", HttpMethod.POST, post_data)
		return BetaBuildLocalization(payload.get('data'), {})

	# TODO: implement POST requests using Resource
	def modify_beta_build_localization(self, beta_build_localization_id, whatsNew):
		post_data = {'data': { 'type': 'betaBuildLocalizations', 'id': beta_build_localization_id, 'attributes': {'whatsNew': whatsNew}}}
		payload = self._api_call(BASE_API +  "/v1/betaBuildLocalizations/" + beta_build_localization_id, HttpMethod.PATCH, post_data)
		return BetaAppLocalization(payload.get('data'), {})

	def list_beta_build_localizations(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_build_localizations
		:return: an iterator over BetaBuildLocalization resources
		"""
		return self._get_resources(BetaBuildLocalization, filters)

	def list_beta_app_review_details(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_app_review_details
		:return: an iterator over BetaAppReviewDetail resources
		"""
		return self._get_resources(BetaAppReviewDetail, filters)

	def list_beta_app_review_submissions(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_app_review_submissions
		:return: an iterator over BetaAppReviewSubmission resources
		"""
		return self._get_resources(BetaAppReviewSubmission, filters)

	# TODO: implement these function using Resource
	def submit_app_for_beta_review(self, build_id):
		post_data = {'data': { 'type': 'betaAppReviewSubmissions', 'relationships': {'build': {'data': {'id': build_id, 'type': 'builds'}}}}}
		payload = self._api_call(BASE_API + "/v1/betaAppReviewSubmissions", HttpMethod.POST, post_data)
		return BetaAppReviewSubmission(payload.get('data'), {})

	# Provisioning
	def list_bundle_ids(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_bundle_ids
		:return: an iterator over BundleId resources
		"""
		return self._get_resources(BundleId, filters, sort)

	def list_certificates(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_and_download_certificates
		:return: an iterator over Certificate resources
		"""
		return self._get_resources(Certificate, filters, sort)

	def list_devices(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_devices
		:return: an iterator over Device resources
		"""
		return self._get_resources(Device, filters, sort)

	# TODO: implement POST requests using Resource
	def register_device(self, name, platform, udid):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/register_a_new_device
		:return: a Device resource
		"""
		post_data = {'data': {'attributes': {'name': name, 'platform': platform, 'udid': udid}, 'type': 'devices'}}
		payload = self._api_call(BASE_API + "/v1/devices", HttpMethod.POST, post_data)
		return Device(payload.get('data'), {})

	def list_profiles(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_and_download_profiles
		:return: an iterator over Profile resources
		"""
		return self._get_resources(Profile, filters, sort)

	# Reporting
	def download_finance_reports(self, filters=None, save_to=None):
		# setup required filters if not provided
		for required_key, default_value in (
				('regionCode', 'ZZ'),
				('reportType', 'FINANCIAL'),
				# vendorNumber is required but we cannot provide a default value
				# reportDate is required but we cannot provide a default value
		):
			if required_key not in filters:
				filters[required_key] = default_value

		url = "%s%s" % (BASE_API, FinanceReport.endpoint)
		url = self._build_query_parameters(url, filters)
		response = self._api_call(url)

		if save_to:
			file = Path(save_to)
			file.write_text(response, 'utf-8')

		return response

	def download_sales_and_trends_reports(self, filters=None, save_to=None):
		# setup required filters if not provided
		for required_key, default_value in (
				('frequency', 'DAILY'),
				('reportSubType', 'SUMMARY'),
				('reportType', 'SALES'),
				# vendorNumber is required but we cannot provide a default value
		):
			if required_key not in filters:
				filters[required_key] = default_value

		url = "%s%s" % (BASE_API, SalesReport.endpoint)
		url = self._build_query_parameters(url, filters)
		response = self._api_call(url)

		if save_to:
			file = Path(save_to)
			file.write_text(response, 'utf-8')

		return response

