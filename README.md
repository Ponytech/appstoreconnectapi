App Store Connect Api
====

This is a Python wrapper around the **Apple App Store Api** : https://developer.apple.com/documentation/appstoreconnectapi

So far, it handles token generation / expiration, methods for listing resources and downloading reports. 

Installation
------------

[![Version](http://img.shields.io/pypi/v/appstoreconnect.svg?style=flat)](https://pypi.org/project/appstoreconnect/)

The project is published on PyPI, install with: 

    pip install appstoreconnect

Usage
-----

Please follow instructions on [Apple documentation](https://developer.apple.com/documentation/appstoreconnectapi/creating_api_keys_for_app_store_connect_api) on how to generate an API key.

With your *key ID*, *key file* and *issuer ID* create a new API instance:

```python
from appstoreconnect import Api
api = Api(key_id, path_to_key_file, issuer_id)
```

Here are a few examples of API usage. For a complete list of available methods please see [api.py](https://github.com/Ponytech/appstoreconnectapi/blob/master/appstoreconnect/api.py#L148).

```python
# list all apps
apps = api.list_apps()
for app in apps:
    print(app.name, app.sku)

# filter apps
apps = api.list_apps(filters={'sku': 'DINORUSH', 'name': 'Dino Rush'})
print("%d apps found" % len(apps))

# read app information
app = api.read_app_information('1308363336')
print(app.name, app.sku, app.bundleId)

# get a related resource
for group in app.betaGroups():
    print(group.name)

# download sales report
api.download_sales_and_trends_reports(
    filters={'vendorNumber': '123456789', 'frequency': 'WEEKLY', 'reportDate': '2019-06-09'}, save_to='report.csv')

# download finance report
api.download_finance_reports(filters={'vendorNumber': '123456789', 'reportDate': '2019-06'}, save_to='finance.csv')
```

Please note this is a work in progress, API is subject to change between versions.


TODO
----

* [ ] handle POST, DELETE and PATCH requests
* [X] sales report
* [X] handle related resources
* [ ] allow to sort resources
* [ ] proper API documentation
* [ ] add tests
* [ ] handle the new "Provisioning" section


Credits
-------

This project is developed by [Ponytech](https://ponytech.net)