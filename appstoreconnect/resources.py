import inspect
from abc import ABC, abstractmethod
import sys


class Resource(ABC):
	relationships = {}

	def __init__(self, data, api):
		self._data = data
		self._api = api

	def __getattr__(self, item):
		if item == 'id':
			return self._data.get('id')
		if item in self._data.get('attributes', {}):
			return self._data.get('attributes', {})[item]
		if item in self.relationships:
			def getter():
				# Try to fetch relationship
				nonlocal item
				url = self._data.get('relationships', {})[item]['links']['related']
				if self.relationships[item]['multiple']:
					return self._api.get_related_resources(full_url=url)
				else:
					return self._api.get_related_resource(full_url=url)
			return getter

		raise AttributeError('%s has no attributes %s' % (self.type_name, item))

	def __repr__(self):
		return '%s id %s' % (self.type_name, self._data.get('id'))

	def __dir__(self):
		return ['id'] + list(self._data.get('attributes', {}).keys()) + list(self._data.get('relationships', {}).keys())

	@property
	def type_name(self):
		return type(self).__name__

	@property
	@abstractmethod
	def endpoint(self):
		pass


# Beta Testers and Groups

class BetaTester(Resource):
	endpoint = '/v1/betaTesters'
	type = 'betaTesters'
	attributes = ['email', 'firstName', 'inviteType', 'lastName']
	relationships = {
		'apps': {'multiple': True},
		'betaGroups': {'multiple': True},
		'builds': {'multiple': True},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betatester'


class BetaGroup(Resource):
	endpoint = '/v1/betaGroups'
	type = 'betaGroups'
	attributes = ['isInternalGroup', 'name', 'publicLink', 'publicLinkEnabled', 'publicLinkId', 'publicLinkLimit', 'publicLinkLimitEnabled', 'createdDate']
	relationships = {
		'app': {'multiple': False},
		'betaTesters': {'multiple': True},
		'builds': {'multiple': True},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betagroup'


# App Resources

class App(Resource):
	endpoint = '/v1/apps'
	type = 'apps'
	attributes = ['bundleId', 'name', 'primaryLocale', 'sku']
	relationships = {
		'betaLicenseAgreement': {'multiple': False},
		'preReleaseVersions': {'multiple': True},
		'betaAppLocalizations': {'multiple': True},
		'betaGroups': {'multiple': True},
		'betaTesters': {'multiple': True},
		'builds': {'multiple': True},
		'betaAppReviewDetail': {'multiple': False},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/app'


class PreReleaseVersion(Resource):
	endpoint = '/v1/preReleaseVersions'
	type = 'preReleaseVersions'
	attributes = ['platform', 'version']
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/preReleaseVersion/attributes'


class BetaAppLocalization(Resource):
	endpoint = '/v1/betaAppLocalizations'
	type = 'betaAppLocalizations'
	attributes = ['description', 'feedbackEmail', 'locale', 'marketingUrl', 'privacyPolicyUrl', 'tvOsPrivacyPolicy']
	relationships = {
		'app': {'multiple': False}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betaAppLocalization/attributes'


class AppEncryptionDeclaration(Resource):
	endpoint = '/v1/appEncryptionDeclarations'
	type = 'appEncryptionDeclarations'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appEncryptionDeclaration/attributes'


class BetaLicenseAgreement(Resource):
	endpoint = '/v1/betaLicenseAgreements'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betaLicenseAgreement/attributes'


# Build Resources

class Build(Resource):
	endpoint = '/v1/builds'
	type = 'builds'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/build/attributes'
	relationships = {
		'app': {'multiple': False},
		'appEncryptionDeclaration': {'multiple': False},
		'individualTesters': {'multiple': True},
		'preReleaseVersion': {'multiple': False},
		'betaBuildLocalizations': {'multiple': True},
		'buildBetaDetail': {'multiple': False},
		'betaAppReviewSubmission': {'multiple': False},
		'appStoreVersion': {'multiple': False},
		'icons': {'multiple': True},
	}


class BuildBetaDetail(Resource):
	endpoint = '/v1/buildBetaDetails'
	type = 'buildBetaDetails'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/buildBetaDetail/attributes'


class BetaBuildLocalization(Resource):
	endpoint = '/v1/betaBuildLocalizations'
	type = 'betaBuildLocalizations'
	attributes = ['locale', 'whatsNew']
	relationships = {
		'build': {'multiple': False},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betaBuildLocalization/attributes'


class BetaAppReviewDetail(Resource):
	endpoint = '/v1/betaAppReviewDetails'
	type = 'betaAppReviewDetails'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betaAppReviewDetail/attributes'


class BetaAppReviewSubmission(Resource):
	endpoint = '/v1/betaAppReviewSubmissions'
	type = 'betaAppReviewSubmissions'
	attributes = ['betaReviewState']
	relationships = {
		'build': {'multiple': False},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betaAppReviewSubmission/attributes'


# Users and Roles

class User(Resource):
	endpoint = '/v1/users'
	type = 'users'
	attributes = ['allAppsVisible', 'provisioningAllowed', 'roles']
	relationships = {
		'visibleApps': {'multiple': True},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/user/attributes'


class UserInvitation(Resource):
	endpoint = '/v1/userInvitations'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/userinvitation/attributes'


# Provisioning
class BundleId(Resource):
	endpoint = '/v1/bundleIds'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/bundleid/attributes'


class Certificate(Resource):
	endpoint = '/v1/certificates'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/certificate/attributes'


class Device(Resource):
	endpoint = '/v1/devices'
	type = 'devices'
	attributes = ['name', 'platform', 'udid', 'status']
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/device/attributes'


class Profile(Resource):
	endpoint = '/v1/profiles'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/profile/attributes'


# Reporting

class FinanceReport(Resource):
	endpoint = '/v1/financeReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_finance_reports'


class SalesReport(Resource):
	endpoint = '/v1/salesReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_sales_and_trends_reports'


# create an index of Resources by type
resources = {}
for name, obj in inspect.getmembers(sys.modules[__name__]):
	if inspect.isclass(obj) and issubclass(obj, Resource) and hasattr(obj, 'type') and obj != Resource:
		resources[getattr(obj, 'type')] = obj
