from abc import ABC, abstractmethod


class Resource(ABC):

	def __init__(self, data):
		self._data = data

	def __getattr__(self, item):
		try:
			return self._data.get('attributes', {})[item]
		except KeyError:
			raise AttributeError('%s have no attributes %s' % (self.type_name, item))

	def __repr__(self):
		return '%s id %s' % (self.type_name, self._data.get('id'))

	def __dir__(self):
		return self._data.get('attributes', {}).keys()

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


class PreReleaseVersions(Resource):
	endpoint = '/v1/preReleaseVersions'
	attributes = 'https://developer.apple.com/documentation/appstoreconnectapi/preReleaseVersion/attributes'


class BetaAppLocalizations(Resource):
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


class BuildBetaDetails(Resource):
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


# Reporting

class FinanceReport(Resource):
	endpoint = '/v1/financeReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_finance_reports'


class SalesReport(Resource):
	endpoint = '/v1/salesReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_sales_and_trends_reports'


