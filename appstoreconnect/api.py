import requests
import jwt
from datetime import datetime, timedelta
import time
import json
from enum import Enum

ALGORITHM = 'ES256'
BASE_API = "https://api.appstoreconnect.apple.com"

class HttpMethod(Enum):
	GET = 1
	POST = 2
	PATCH = 3

class AppStoreState(Enum):
	DEVELOPER_REMOVED_FROM_SALE = "DEVELOPER_REMOVED_FROM_SALE"
	DEVELOPER_REJECTED = "DEVELOPER_REJECTED"
	IN_REVIEW = "IN_REVIEW"
	INVALID_BINARY = "INVALID_BINARY"
	METADATA_REJECTED = "METADATA_REJECTED"
	PENDING_APPLE_RELEASE = "PENDING_APPLE_RELEASE"
	PENDING_CONTRACT = "PENDING_CONTRACT"
	PENDING_DEVELOPER_RELEASE = "PENDING_DEVELOPER_RELEASE"
	PREPARE_FOR_SUBMISSION = "PREPARE_FOR_SUBMISSION"
	PREORDER_READY_FOR_SALE = "PREORDER_READY_FOR_SALE"
	PROCESSING_FOR_APP_STORE = "PROCESSING_FOR_APP_STORE"
	READY_FOR_SALE = "READY_FOR_SALE"
	REJECTED = "REJECTED"
	REMOVED_FROM_SALE = "REMOVED_FROM_SALE"
	WAITING_FOR_EXPORT_COMPLIANCE = "WAITING_FOR_EXPORT_COMPLIANCE"
	WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
	REPLACED_WITH_NEW_VERSION = "REPLACED_WITH_NEW_VERSION"

	@staticmethod
	def editableStates():
		return list(map(lambda x: x.name, [AppStoreState.DEVELOPER_REJECTED, AppStoreState.INVALID_BINARY, AppStoreState.METADATA_REJECTED, AppStoreState.PREPARE_FOR_SUBMISSION, AppStoreState.REJECTED]))


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

	def _api_call(self, route, method, post_data):
		headers = {"Authorization": "Bearer %s" % self.token}
		url = "%s%s" % (BASE_API, route)
		r = {}

		if method == HttpMethod.GET:
			r = requests.get(url, headers=headers)
		elif method == HttpMethod.POST:
			headers["Content-Type"] = "application/json"
			r = requests.post(url=url, headers=headers, data=json.dumps(post_data))
		elif method == HttpMethod.PATCH:
			headers["Content-Type"] = "application/json"
			r = requests.patch(url=url, headers=headers, data=json.dumps(post_data))

		contentType = r.headers['content-type']

		if r.status_code not in range(200,299):
			print("Error [%d][%s]" % (r.status_code, r.content))

		if contentType == "application/json":
			return r.json()

	#apps

	def apps(self):
		return self._api_call("/v1/apps", HttpMethod.GET, None)

	def app_for_sku(self, sku):
		return self._api_call("/v1/apps?filter[sku]=" + sku, HttpMethod.GET, None)

	def app_for_bundleId(self, bundle_id):
		return self._api_call("/v1/apps?filter[bundleId]=" + bundle_id, HttpMethod.GET, None)

	#users

	def users(self):
		return self._api_call("/v1/users", HttpMethod.GET, None)

	#userInvitations

	def user_invitations(self):
		return self._api_call("/v1/userInvitations", HttpMethod.GET, None)

	#betaGroups

	def beta_groups(self, app_id):
		return self._api_call("/v1/apps/" + app_id + "/betaGroups", HttpMethod.GET, None)

	def create_beta_group(self, group_name, app_id):
		post_data = {'data': {'attributes': {'name': group_name}, 'relationships': {'app': {'data': {'id': app_id, 'type': 'apps'}}}, 'type': 'betaGroups'}}

		return self._api_call("/v1/betaGroups", HttpMethod.POST, post_data)

	def activate_public_link_for_beta_group(self, beta_group_id):
		post_data = {'data': {'attributes': {'publicLinkEnabled': True}, 'id': beta_group_id, 'type': 'betaGroups'}}

		return self._api_call("/v1/betaGroups/" + beta_group_id, HttpMethod.PATCH, post_data)

	def beta_group_info(self, beta_group_id):
		return self._api_call("/v1/betaGroups/" + beta_group_id, HttpMethod.GET, None)

	def add_build_to_beta_group(self, beta_group_id, build_id):
		post_data = {'data': [{ 'id': build_id, 'type': 'builds'}]}

		return self._api_call("/v1/betaGroups/" + beta_group_id + "/relationships/builds", HttpMethod.POST, post_data)

	#betaTesters

	def beta_testers(self):
		return self._api_call("/v1/betaTesters", HttpMethod.GET, None)

	def create_beta_tester(self, beta_group_id, email, first_name, last_name):
		post_data = {'data': {'attributes': {'email': email, 'firstName': first_name, 'lastName': last_name}, 'relationships': {'betaGroups': {'data': [{ 'id': beta_group_id ,'type': 'betaGroups'}]}}, 'type': 'betaTesters'}}

		return self._api_call("/v1/betaTesters", HttpMethod.POST, post_data)

	def beta_group_beta_testers(self, beta_group_id):
		return self._api_call("/v1/betaGroups/" + beta_group_id + "/betaTesters", HttpMethod.GET, None)

	#prereleaseVersions

	def prerelease_versions_id_for_app_and_version(self, app_id, version):
		return self._api_call("/v1/preReleaseVersions?filter[app]=" + app_id + "&filter[version]=" + version, HttpMethod.GET, None)

	#builds

	def build_prerelease_version(self, build_id):
		return self._api_call("/v1/builds/" + build_id + "/preReleaseVersion", HttpMethod.GET, None)

	def builds(self):
		return self._api_call("/v1/builds", HttpMethod.GET, None)

	def builds_for_app(self, app_id):
		return self._api_call("/v1/builds?include=preReleaseVersion&filter[app]=" + app_id, HttpMethod.GET, None)

	def builds_for_app_and_version_and_prerelease_version(self, app_id, version, prerelease_version):
		return self._api_call("/v1/builds?filter[app]=" + app_id + "&filter[version]=" + version + "&filter[preReleaseVersion]=" + prerelease_version, HttpMethod.GET, None)

	def builds_for_app_and_version_and_prerelease_version_version(self, app_id, prerelease_version_version, version):
		return self._api_call("/v1/builds?filter[app]=" + app_id + "&filter[version]=" + version + "&filter[preReleaseVersion.version]=" + prerelease_version_version, HttpMethod.GET, None)

	def build_processing_state(self, app_id, build_id):
		return self._api_call("/v1/builds?filter[app]=" + app_id + "&filter[id]=" + build_id + "&fields[builds]=processingState", HttpMethod.GET, None)

	def set_uses_non_encryption_exemption_setting(self, build_id, uses_non_encryption_exemption_setting):
		post_data = {'data': {'attributes': {'usesNonExemptEncryption': uses_non_encryption_exemption_setting}, 'id': build_id, 'type': 'builds'}}
		return self._api_call("/v1/builds/" + build_id, HttpMethod.PATCH, post_data)

	#betaBuildLocalizations

	def beta_build_localizations_for_build(self, build_id):
		return self._api_call("/v1/betaBuildLocalizations?filter[build]=" + build_id, HttpMethod.GET, None)

	def beta_build_localizations_for_build_and_locale(self, build_id, locale):
		return self._api_call("/v1/betaBuildLocalizations?filter[build]=" + build_id + "&filter[locale]=" + locale, HttpMethod.GET, None)

	def create_beta_build_localization(self, build_id, locale, whatsNew):
		post_data = {'data': { 'type': 'betaBuildLocalizations', 'relationships': {'build': {'data': {'id': build_id, 'type': 'builds'}}}, 'attributes': { 'locale': locale, 'whatsNew': whatsNew}}}
		return self._api_call("/v1/betaBuildLocalizations", HttpMethod.POST, post_data)

	def modify_beta_build_localization(self, beta_build_localization_id, whatsNew):
		post_data = {'data': { 'type': 'betaBuildLocalizations', 'id': beta_build_localization_id, 'attributes': {'whatsNew': whatsNew}}}
		return self._api_call("/v1/betaBuildLocalizations/" + beta_build_localization_id, HttpMethod.PATCH, post_data)

	#betaAppReviewSubmissions

	def submit_app_for_beta_review(self, build_id):
		post_data = {'data': { 'type': 'betaAppReviewSubmissions', 'relationships': {'build': {'data': {'id': build_id, 'type': 'builds'}}}}}
		return self._api_call("/v1/betaAppReviewSubmissions", HttpMethod.POST, post_data)

	def beta_appreview_submission(self, appreview_id):
		return self._api_call("/v1/betaAppReviewSubmissions/" + appreview_id, HttpMethod.GET, None)

	#territories

	def territories(self):
		return self._api_call("/v1/territories", HttpMethod.GET, None)

	#build icons
	def build_icons_for_build(self, build_id):
		return self._api_call("/v1/builds/" + build_id+ "/icons", HttpMethod.GET, None)

	#appstore versions
	def appstoreversions_for_app(self, app_id):
		return self._api_call("/v1/apps/" + app_id+ "/appStoreVersions", HttpMethod.GET, None)

	def create_new_version_for_app(self, versionString, app_id):
		post_data = {'data': { 'type': 'appStoreVersions', 'relationships': {'app': {'data': {'id': app_id, 'type': 'apps'}}}, 'attributes': { 'platform': 'IOS', 'versionString': versionString}}}
		return self._api_call("/v1/appStoreVersions", HttpMethod.POST, post_data)

	def update_appstoreversion(self, appstoreversion_id, attributes, relationships):
		post_data = {'data': { 'id': appstoreversion_id, 'type': 'appStoreVersions', 'attributes': attributes , 'relationships': relationships }}
		return self._api_call("/v1/appStoreVersions/" + appstoreversion_id, HttpMethod.PATCH, post_data)

	def update_versionString_for_appstoreversion(self, appstoreversion_id, versionString):
		attributes = { 'versionString': versionString }
		self.update_appstoreversion(appstoreversion_id, attributes, {})

	def associate_build_to_appstoreversion(self, build_id, appstoreversion_id):
		post_data = {'data': { 'id': build_id, 'type': 'builds' }}
		return self._api_call("/v1/appStoreVersions/" + appstoreversion_id + "/relationships/build", HttpMethod.PATCH, post_data)

	def idfadeclaration_for_appstoreversion(self, appstoreversion_id):
		return self._api_call("/v1/appStoreVersions/" + appstoreversion_id+ "/idfaDeclaration", HttpMethod.GET, None)


	@property
	def token(self):
		# generate a new token every 15 minutes
		if not self._token or self.token_gen_date + timedelta(minutes=15) > datetime.now():
			self._token = self._generate_token()

		return self._token
