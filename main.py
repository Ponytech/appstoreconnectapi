#!/usr/bin/env python

import sys
from appstoreconnect import Api
from appstoreconnect import AppStoreState


if __name__ == "__main__":
	key_id = sys.argv[1]
	key_file = sys.argv[2]
	issuer_id = sys.argv[3]
	api = Api(key_id, key_file, issuer_id)

	app = api.app_for_bundleId("com.orange.fr.orangeetmoi")
	app_id = app["data"][0]["id"]
	appstoreversions = api.appstoreversions_for_app(app_id)
	appstoreversion_id = appstoreversions["data"][0]["id"]
	#appstorestate = appstoreversions["data"][0]["attributes"]["appStoreState"]

	#print(appstoreversions["data"][0])
	#builds = api.builds_for_app_and_version_and_prerelease_version_version(app_id, "1.0.0", "4")
	#build_id = builds["data"][0]["id"]
	#icons = api.build_icons_for_build(build_id)

	#if appstorestate in AppStoreState.editableStates():
		#r = api.update_idfaUse_for_appstoreversion(appstoreversion_id, True)
		#print(r)

	r = api.idfadeclaration_for_appstoreversion(appstoreversion_id)
	print(r)
	r = api.update_idfaUse_for_appstoreversion(appstoreversion_id, False, True)
	print(r)
