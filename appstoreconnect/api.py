import requests
import jwt
import gzip
import platform
import hashlib
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta
import time
import json
from enum import Enum

from .resources import *
from .__version__ import __version__ as version

ALGORITHM = 'ES256'
BASE_API = "https://api.appstoreconnect.apple.com"


class HttpMethod(Enum):
	GET = 1
	POST = 2
	PATCH = 3
	DELETE = 4


class APIError(Exception):
	def __init__(self, error_string, status_code):
		try:
			self.status_code = int(status_code)
		except ValueError:
			pass
		super().__init__(error_string)


class Api:

	def __init__(self, key_id, key_file, issuer_id, submit_stats=True):
		self._token = None
		self.token_gen_date = None
		self.exp = None
		self.key_id = key_id
		self.key_file = key_file
		self.issuer_id = issuer_id
		self.submit_stats = submit_stats
		self._call_stats = defaultdict(int)
		if self.submit_stats:
			self._submit_stats("session_start")

		self._debug = False
		token = self.token  # generate first token

	def __del__(self):
		if self.submit_stats:
			self._submit_stats("session_end")

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

	def _create_resource(self, Resource, args):
		attributes = {}
		for attribute in Resource.attributes:
			if attribute in args and args[attribute] is not None:
				attributes[attribute] = args[attribute]

		relationships_dict = {}
		for relation in Resource.relationships.keys():
			if relation in args and args[relation] is not None:
				relationships_dict[relation] = {}
				if Resource.relationships[relation].get('multiple', False):
					relationships_dict[relation]['data'] = []
					relationship_objects = args[relation]
					if type(relationship_objects) is not list:
						relationship_objects = [relationship_objects]
					for relationship_object in relationship_objects:
						relationships_dict[relation]['data'].append({
							'id': relationship_object.id,
							'type': relationship_object.type
						})
				else:
					relationships_dict[relation]['data'] = {
							'id': args[relation].id,
							'type': args[relation].type
						}

		post_data = {
			'data': {
				'attributes': attributes,
				'relationships': relationships_dict,
				'type': Resource.type
			}
		}
		url = "%s%s" % (BASE_API, Resource.endpoint)
		if self._debug:
			print(post_data)
		payload = self._api_call(url, HttpMethod.POST, post_data)

		return Resource(payload.get('data', {}), self)

	def _modify_resource(self, resource, args):
		attributes = {}
		for attribute in resource.attributes:
			if attribute in args and args[attribute] is not None:
				attributes[attribute] = args[attribute]

		post_data = {
			'data': {
				'attributes': attributes,
				'id': resource.id,
				'type': resource.type
			}
		}
		url = "%s%s/%s" % (BASE_API, resource.endpoint, resource.id)
		if self._debug:
			print(post_data)
		payload = self._api_call(url, HttpMethod.PATCH, post_data)

		return type(resource)(payload.get('data', {}), self)

	def _delete_resource(self, resource: Resource):
		url = "%s%s/%s" % (BASE_API, resource.endpoint, resource.id)
		self._api_call(url, HttpMethod.DELETE)

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

		if self._submit_stats:
			endpoint = url.replace(BASE_API, '')
			if method in (HttpMethod.PATCH, HttpMethod.DELETE):  # remove last bit of endpoint which is a resource id
				endpoint = "/".join(endpoint.split('/')[:-1])
			request = "%s %s" % (method.name, endpoint)
			self._call_stats[request] += 1

		if method == HttpMethod.GET:
			r = requests.get(url, headers=headers)
		elif method == HttpMethod.POST:
			headers["Content-Type"] = "application/json"
			r = requests.post(url=url, headers=headers, data=json.dumps(post_data))
		elif method == HttpMethod.PATCH:
			headers["Content-Type"] = "application/json"
			r = requests.patch(url=url, headers=headers, data=json.dumps(post_data))
		elif method == HttpMethod.DELETE:
			r = requests.delete(url=url, headers=headers)
		else:
			raise APIError("Unknown HTTP method")

		content_type = r.headers['content-type']

		if content_type in [ "application/json", "application/vnd.api+json" ]:
			payload = r.json()
			if 'errors' in payload:
				raise APIError(
					payload.get('errors', [])[0].get('detail', 'Unknown error'),
				 	payload.get('errors', [])[0].get('status', None)
				)
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

	def _submit_stats(self, event_type):
		"""
		this submits anonymous usage statistics to help us better understand how this library is used
		you can opt-out by initializing the client with submit_stats=False
		"""
		payload = {
			'project': 'appstoreconnectapi',
			'version': version,
			'type': event_type,
			'parameters': {
				'python_version': platform.python_version(),
				'platform': platform.platform(),
				'issuer_id_hash': hashlib.sha1(self.issuer_id.encode()).hexdigest(),  # send anonymized hash
			}
		}
		if event_type == 'session_end':
			payload['parameters']['endpoints'] = self._call_stats
		requests.post('https://stats.ponytech.net/new-event', json.dumps(payload))

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
			visible_apps_relationship = list(map(lambda a: {'id': a, 'type': 'apps'}, visible_apps))
			visible_apps_data = {'visibleApps': {'data': visible_apps_relationship}}
			post_data['data']['relationships'] = visible_apps_data
		payload = self._api_call(BASE_API + "/v1/userInvitations", HttpMethod.POST, post_data)
		return UserInvitation(payload.get('data'), {})

	def read_user_invitation_information(self, user_invitation_id: str):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/read_user_invitation_information
		:return: a UserInvitation resource
		"""
		return self._get_resource(UserInvitation, user_invitation_id)

	# Beta Testers and Groups
	def create_beta_tester(self, email: str, firstName: str = None, lastName: str = None, betaGroups: BetaGroup = None, builds: Build = None) -> BetaTester:
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/create_a_beta_tester
		:return: an BetaTester resource
		"""
		return self._create_resource(BetaTester, locals())

	def delete_beta_tester(self, betaTester: BetaTester) -> None:
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/delete_a_beta_tester
		:return: None
		"""
		return self._delete_resource(betaTester)

	def list_beta_testers(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_testers
		:return: an iterator over BetaTester resources
		"""
		return self._get_resources(BetaTester, filters, sort)

	def read_beta_tester_information(self, beta_tester_id: str):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/read_beta_tester_information
		:return: a BetaTester resource
		"""
		return self._get_resource(BetaTester, beta_tester_id)

	def create_beta_group(self, app: App, name: str, publicLinkEnabled: bool = None, publicLinkLimit: int = None, publicLinkLimitEnabled: bool = None) -> BetaGroup:
		"""
		:reference:https://developer.apple.com/documentation/appstoreconnectapi/create_a_beta_group
		:return: a BetaGroup resource
		"""
		return self._create_resource(BetaGroup, locals())

	def modify_beta_group(self, betaGroup: BetaGroup, name: str = None, publicLinkEnabled: bool = None, publicLinkLimit: int = None, publicLinkLimitEnabled: bool = None) -> BetaGroup:
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/modify_a_beta_group
		:return: a BetaGroup resource
		"""
		return self._modify_resource(betaGroup, locals())

	def delete_beta_group(self, betaGroup: BetaGroup):
		return self._delete_resource(betaGroup)

	def list_beta_groups(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_groups
		:return: an iterator over BetaGroup resources
		"""
		return self._get_resources(BetaGroup, filters, sort)

	def read_beta_group_information(self, beta_group_ip):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/read_beta_group_information
		:return: an BetaGroup resource
		"""
		return self._get_resource(BetaGroup, beta_group_ip)

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

	def read_beta_app_localization_information(self, beta_app_id: str):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/read_beta_app_localization_information
		:return: an BetaAppLocalization resource
		"""
		return self._get_resource(BetaAppLocalization, beta_app_id)

	def create_beta_app_localization(self, app: App, locale: str, description: str = None, feedbackEmail: str = None, marketingUrl: str = None, privacyPolicyUrl: str = None, tvOsPrivacyPolicy: str = None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/create_a_beta_app_localization
		:return: an BetaAppLocalization resource
		"""
		return self._create_resource(BetaAppLocalization, locals())

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

	def create_beta_build_localization(self, build: Build, locale: str, whatsNew: str = None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/create_a_beta_build_localization
		:return: a BetaBuildLocalization resource
		"""
		return self._create_resource(BetaBuildLocalization, locals())

	def modify_beta_build_localization(self, beta_build_localization: BetaBuildLocalization, whatsNew: str):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/modify_a_beta_build_localization
		:return: a BetaBuildLocalization resource
		"""
		return self._modify_resource(beta_build_localization, locals())

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

	def submit_app_for_beta_review(self, build: Build) -> BetaAppReviewSubmission:
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/submit_an_app_for_beta_review
		:return: a BetaAppReviewSubmission resource
		"""

		return self._create_resource(BetaAppReviewSubmission, locals())

	def list_beta_app_review_submissions(self, filters=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_beta_app_review_submissions
		:return: an iterator over BetaAppReviewSubmission resources
		"""
		return self._get_resources(BetaAppReviewSubmission, filters)

	def read_beta_app_review_submission_information(self, beta_app_id: str):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/read_beta_app_review_submission_information
		:return: an BetaAppReviewSubmission resource
		"""
		return self._get_resource(BetaAppReviewSubmission, beta_app_id)

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

	def register_new_device(self, name: str, platform: str, udid: str) -> Device:
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/register_a_new_device
		:return: a Device resource
		"""
		return self._create_resource(Device, locals())

	def modify_registered_device(self, device: Device, name: str = None, status: str = None) -> Device:
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/modify_a_registered_device
		:return: a Device resource
		"""
		return self._modify_resource(device, locals())

	def list_profiles(self, filters=None, sort=None):
		"""
		:reference: https://developer.apple.com/documentation/appstoreconnectapi/list_and_download_profiles
		:return: an iterator over Profile resources
		"""
		return self._get_resources(Profile, filters, sort)

	# Reporting
	def download_finance_reports(self, filters=None, split_response=False, save_to=None):
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

		if split_response:
			res1 = response.split('Total_Rows')[0]
			res2 = '\n'.join(response.split('Total_Rows')[1].split('\n')[1:])

			if save_to:
				file1 = Path(save_to[0])
				file1.write_text(res1, 'utf-8')
				file2 = Path(save_to[1])
				file2.write_text(res2, 'utf-8')

			return res1, res2

		if save_to:
			file = Path(save_to)
			file.write_text(response, 'utf-8')

		return response

	def download_sales_and_trends_reports(self, filters=None, save_to=None):
		# setup required filters if not provided
		default_versions = {
			'SALES': '1_0',
			'SUBSCRIPTION': '1_2',
			'SUBSCRIPTION_EVENT': '1_2',
			'SUBSCRIBER': '1_2',
			'NEWSSTAND': '1_0',
			'PRE_ORDER': '1_0',
		}
		default_subtypes = {
			'SALES': 'SUMMARY',
			'SUBSCRIPTION': 'SUMMARY',
			'SUBSCRIPTION_EVENT': 'SUMMARY',
			'SUBSCRIBER': 'DETAILED',
			'NEWSSTAND': 'DETAILED',
			'PRE_ORDER': 'SUMMARY',
		}
		for required_key, default_value in (
				('frequency', 'DAILY'),
				('reportType', 'SALES'),
				('reportSubType',  default_subtypes.get(filters.get('reportType', 'SALES'), 'SUMMARY')),
				('version', default_versions.get(filters.get('reportType', 'SALES'), '1_0')),
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
