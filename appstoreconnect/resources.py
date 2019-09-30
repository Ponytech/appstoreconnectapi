from abc import ABC, abstractmethod
import sys

class Resource(ABC):

	def __init__(self, data, api):
		self._data = data
		self._api = api

	def __getattr__(self, item):
		if item == 'id':
			return self._data.get('id')
		if item in self._data.get('attributes', {}):
			return self._data.get('attributes', {})[item]
		if item in self._data.get('relationships', {}):
			def callable():
				# Try to fetch relationship
				nonlocal item
				is_resources = item[-1] == 's'
				try:
					item_cls = getattr(sys.modules[__name__], item[0].upper() + (item[1:-1] if is_resources else item[1:]))
				except AttributeError:
					item_cls = Resource
				url = self._data.get('relationships', {})[item]['links']['related']
				# List of resources
				if is_resources:
					return self._api._get_resources(item_cls, full_url=url)
				else:
					return self._api._get_related_resource(item_cls, full_url=url)
			return callable

		raise AttributeError('%s have no attributes %s' % (self.type_name, item))

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
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/betatester/attributes'


class BetaGroup(Resource):
	endpoint = '/v1/betaGroups'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/betagroup/attributes'


# App Resources

class App(Resource):
	endpoint = '/v1/apps'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/app/attributes'


class PreReleaseVersion(Resource):
	endpoint = '/v1/preReleaseVersions'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/preReleaseVersion/attributes'


class BetaAppLocalization(Resource):
	endpoint = '/v1/betaAppLocalizations'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/betaAppLocalization/attributes'


class AppEncryptionDeclaration(Resource):
	endpoint = '/v1/appEncryptionDeclarations'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/appEncryptionDeclaration/attributes'


class BetaLicenseAgreement(Resource):
	endpoint = '/v1/betaLicenseAgreements'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/betaLicenseAgreement/attributes'


# Build Resources

class Build(Resource):
	endpoint = '/v1/builds'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/build/attributes'


class BuildBetaDetail(Resource):
	endpoint = '/v1/buildBetaDetails'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/buildBetaDetail/attributes'


class BetaBuildLocalization(Resource):
	endpoint = '/v1/betaBuildLocalizations'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/betaBuildLocalization/attributes'


class BetaAppReviewDetail(Resource):
	endpoint = '/v1/betaAppReviewDetails'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/betaAppReviewDetail/attributes'


class BetaAppReviewSubmission(Resource):
	endpoint = '/v1/betaAppReviewDetails'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/betaAppReviewSubmission/attributes'


# Users and Roles

class User(Resource):
	endpoint = '/v1/users'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/user/attributes'


class UserInvitation(Resource):
	endpoint = '/v1/userInvitations'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/userinvitation/attributes'


# Provisioning
class BundleId(Resource):
	endpoint = '/v1/bundleIds'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/bundleid/attributes'


class Certificate(Resource):
	endpoint = '/v1/certificates'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/certificate/attributes'


class Device(Resource):
	endpoint = '/v1/devices'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/device/attributes'


class Profile(Resource):
	endpoint = '/v1/profiles'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/profile/attributes'


# Reporting

class FinanceReport(Resource):
	endpoint = '/v1/financeReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_finance_reports'


class SalesReport(Resource):
	endpoint = '/v1/salesReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_sales_and_trends_reports'
