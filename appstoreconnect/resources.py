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
	type = 'betaTesters'
	attributes = ['email', 'firstName', 'inviteType', 'lastName']
	relationships = {
		'apps': {'multiple': True},
		'betaGroups': {'multiple': True},
		'builds': {'multiple': True},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/betatester'

class BetaTesterInvitation(Resource):
	endpoint = '/v1/betaTesterInvitations'
	type = 'betaTesterInvitations'
	attributes = []
	relationships = {
		'app': {'multiple': False},
		'betaTester': {'multiple': False}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/BetaTesterInvitation'

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



# App Metadata Resources

class AppScreenshot(Resource):
	endpoint = '/v1/appScreenshots'
	type = 'appScreenshots'
	attributes = ['assetDeliveryState', 'assetToken', 'assetType', 'fileName', 'fileSize', 'imageAsset', 'sourceFileChecksum', 'uploadOperations', 'uploaded']
	relationships = {
		'appScreenshotSet': {'multiple': False}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appscreenshot'

class AppScreenshotSet(Resource):
	endpoint = '/v1/appScreenshotSets'
	type = 'appScreenshotSets'
	attributes = ['screenshotDisplayType']
	relationships = {
		'appScreenshots': {'multiple': True},
		'appStoreVersionLocalization': {'multiple': False}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appscreenshotset'

class AppStoreVersionLocalization(Resource):
	endpoint = '/v1/appStoreVersionLocalizations'
	type = 'appStoreVersionLocalizations'
	attributes = ['description', 'keywords', 'locale', 'marketingUrl', 'promotionalText', 'supportUrl', 'whatsNew']
	relationships = {
		'appPreviewSets': {'multiple': True},
		'appScreenshotSets': {'multiple': True},
		'appStoreVersion': {'multiple': False}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appstoreversionlocalization'

class AgeRatingDeclarations(Resource):
	endpoint = '/v1/ageRatingDeclarations'
	attributes = ['alcoholTobaccoOrDrugUseOrReferences', 'gamblingAndContests', 'kidsAgeBand', 'medicalOrTreatmentInformation',
	'profanityOrCrudeHumor', 'sexualContentOrNudity', 'unrestrictedWebAccess', 'gamblingSimulated', 'horrorOrFearThemes',
	'matureOrSuggestiveThemes', 'sexualContentGraphicAndNudity', 'violenceCartoonOrFantasy', 'violenceRealistic', 'violenceRealisticProlongedGraphicOrSadistic']
	relationships = {}
	type = 'ageRatingDeclarations'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/ageratingdeclaration'

class AppStoreVersion(Resource):
	endpoint = '/v1/appStoreVersions'
	type = 'appStoreVersions'
	attributes = ['platform', 'appStoreState', 'copyright', 'earliestReleaseDate', 'releaseType', 'usesIdfa', 'versionString', 'downloadable', 'createdDate']
	relationships = {
		'app': {'multiple': False},
		'ageRatingDeclaration': {'multiple': False},
		'appStoreReviewDetail': {'multiple': False},
		'appStoreVersionLocalizations': {'multiple': True},
		'appStoreVersionPhasedRelease': {'multiple': False},
		'appStoreVersionSubmission': {'multiple': False},
		'build': {'multiple': False},
		'idfaDeclaration': {'multiple': False},
		'routingAppCoverage': {'multiple': False},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appstoreversion'

class AgeRatingDeclaration(Resource):
	endpoint = '/v1/ageRatingDeclarations'
	type = "ageRatingDeclarations"
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/ageratingdeclaration'

class Territory(Resource):
	endpoint = '/v1/territories'
	type = 'territories'
	attributes = 'currency'
	relationships = {}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/territory'


class AppStoreReviewDetail(Resource):
	endpoint = '/v1/appStoreReviewDetails'
	type = "appStoreReviewDetails"
	attributes = ['contactEmail', 'contactFirstName', 'contactLastName', 'contactPhone', 'demoAccountName', 'demoAccountPassword', 'demoAccountRequired', 'notes']
	relationships = {
		'appStoreVersion': {'multiple': False},
		'appStoreReviewAttachments': {'multiple': True}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appstorereviewdetail'

class AppStoreVersionLocalizations(Resource):
	endpoint = '/v1/appStoreVersionLocalizations'
	type = "appStoreVersionLocalizations"
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appstoreversionlocalization'

class AppStoreVersionSubmission(Resource):
	endpoint = '/v1/appStoreVersionSubmissions'
	type = "appStoreVersionSubmissions"
	attributes = []
	relationships = {
		'appStoreVersion': {'multiple': False}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appstoreversionsubmission'

class IdfaDeclaration(Resource):
	endpoint = '/v1/idfaDeclarations'
	type = "idfaDeclarations"
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/idfadeclaration'

class RoutingAppCoverage(Resource):
	endpoint = '/v1/routingAppCoverages'
	type = "routingAppCoverages"
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/routingappcoverages'

class AppInfoLocalization(Resource):
	endpoint = '/v1/appInfoLocalizations'
	type = 'appInfoLocalizations'
	attributes = ['locale', 'name', 'privacyPolicyText', 'privacyPolicyUrl', 'subtitle']
	relationships = {
		'appInfo': {'multiple': False},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appinfolocalization'

class AppStoreVersionPhasedRelease(Resource):
	endpoint = '/v1/appStoreVersionPhasedReleases'
	type = 'appStoreVersionPhasedReleases'
	attributes = ['currentDayNumber', 'phasedReleaseState', 'startDate', 'totalPauseDuration']
	relationships = {
		'appStoreVersion': {'multiple': False},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appstoreversionphasedrelease'

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
	type = 'preReleaseVersion'
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
	attributes = ['expired', 'iconAssetToken', 'minOsVersion', 'processingState', 'version', 'usesNonExemptEncryption', 'uploadedDate', 'expirationDate']
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/build/attributes'


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
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/user/attributes'


class UserInvitation(Resource):
	endpoint = '/v1/userInvitations'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/userinvitation/attributes'


# Provisioning
class BundleId(Resource):
	endpoint = '/v1/bundleIds'
	type = 'bundleIds'
	attributes = ['identifier', 'name', 'platform', 'seedId']
	relationships = {
		'profiles': {'multiple': True},
		'bundleIdCapabilities': {'multiple': True},
		'app': {'multiple': False},
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/bundleid/attributes'


class Certificate(Resource):
	endpoint = '/v1/certificates'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/certificate/attributes'


class Device(Resource):
	endpoint = '/v1/devices'
	type = 'devices'
	attributes = ['name', 'platform', 'udid', 'status']
	relationships = {
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/device/attributes'


class Profile(Resource):
	endpoint = '/v1/profiles'
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/profile/attributes'
	type = 'profiles'
	attributes = ['name', 'platform', 'profileContent', 'uuid', 'createdDate', 'profileState', 'profileType', 'expirationDate']
	relationships = {
		'certificates': {'multiple': True},
		'devices': {'multiple': True},
		'bundleId': {'multiple': False},
	}

# Reporting

class FinanceReport(Resource):
	endpoint = '/v1/financeReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_finance_reports'


class SalesReport(Resource):
	endpoint = '/v1/salesReports'
	filters = 'https://developer.apple.com/documentation/appstoreconnectapi/download_sales_and_trends_reports'

class AppCategory(Resource):
	endpoint = '/v1/appCategories'
	type = 'appCategories'
	attributes = ['platforms']
	relationships = {
		'parent': {'multiple': False},
		'subcategories': {'multiple': True}
	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appcategory'

class AppInfo(Resource):
	endpoint = '/v1/appInfos'
	type = 'appInfos'
	attributes = ['appStoreAgeRating', 'appStoreState', 'brazilAgeRating', 'kidsAgeBand']
	relationships = {
		'app': {'multiple': False},
		'appInfoLocalizations': {'multiple': True},
		'primaryCategory': {'multiple': False},
		'primarySubcategoryOne': {'multiple': False},
		'primarySubcategoryTwo': {'multiple': False},
		'secondaryCategory': {'multiple': False},
		'secondarySubcategoryOne': {'multiple': False},
		'secondarySubcategoryTwo': {'multiple': False}

	}
	documentation = 'https://developer.apple.com/documentation/appstoreconnectapi/appinfo'
