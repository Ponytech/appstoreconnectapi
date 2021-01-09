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

With your *key ID*, *key file* (you can either pass the path to the file or the content of it as a string) and *issuer ID* create a new API instance:

```python
from appstoreconnect import Api, UserRole
api = Api(key_id, path_to_key_file, issuer_id)
```

Here are a few examples of API usage. For a complete list of available methods please see [api.py](https://github.com/Ponytech/appstoreconnectapi/blob/master/appstoreconnect/api.py#L148).

```python
# list all apps
apps = api.list_apps()
for app in apps:
    print(app.name, app.sku)

# sort resources
apps = api.list_apps(sort='name')

# filter apps
apps = api.list_apps(filters={'sku': 'DINORUSH', 'name': 'Dino Rush'})
print("%d apps found" % len(apps))

# read app information
app = api.read_app_information('1308363336')
print(app.name, app.sku, app.bundleId)

# get a related resource
for group in app.betaGroups():
    print(group.name)

# list bundle ids
for bundle_id in api.list_bundle_ids():
    print(bundle_id.identifier)

# list certificates
for certificate in api.list_certificates():
    print(certificate.name)

# modify a user
user = api.list_users(filters={'username': 'finance@nemoidstudio.com'})[0]
api.modify_user_account(user, roles=[UserRole.FINANCE, UserRole.ACCESS_TO_REPORTS])
    
# download sales report
api.download_sales_and_trends_reports(
    filters={'vendorNumber': '123456789', 'frequency': 'WEEKLY', 'reportDate': '2019-06-09'}, save_to='report.csv')

# download finance report
api.download_finance_reports(filters={'vendorNumber': '123456789', 'reportDate': '2019-06'}, save_to='finance.csv')
```

Please note this is a work in progress, API is subject to change between versions.

Anonymous data collection
-------------------------

Starting with version 0.8.0 this library anonymously collects its usage to help better improve its development. 
What we collect is:

- a SHA1 hash of the issuer_id
- the OS and Python version used
- which enpoints had been used

You can review the [source code](https://github.com/Ponytech/appstoreconnectapi/blob/b73d4314e2a9f9098f3287f57fff687563e70b28/appstoreconnect/api.py#L238)

If you feel uncomfortable with it you can completely opt-out by initliazing the API with:

```python
api = Api(key_id, path_to_key_file, issuer_id, submit_stats=False)
```

The is also an [open issue](https://github.com/Ponytech/appstoreconnectapi/issues/18) about this topic where we would love to here your feedback and best practices.


Development
-----------

Project development happens on [Github](https://github.com/Ponytech/appstoreconnectapi) 


TODO
----

* [ ] Support App Store Connect API 1.2
* [ ] Support the include parameter
* [X] handle POST, DELETE and PATCH requests
* [X] sales report
* [X] handle related resources
* [X] allow to sort resources
* [ ] proper API documentation
* [ ] add tests


Credits
-------

This project is developed by [Ponytech](https://ponytech.net)
