#!/usr/bin/env python

import sys
from AppstoreConnect import Api


if __name__ == "__main__":
	key_id = sys.argv[1]
	key_file = sys.argv[2]
	issuer_id = sys.argv[3]
	api = Api(key_id, key_file, issuer_id)
	apps = api.apps()

	for app in apps["data"]:
		print(app["attributes"]["name"])
