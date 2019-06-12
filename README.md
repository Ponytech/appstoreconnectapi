App Store Connect Api
====

This is Python a wrapper around the Apple App Store Api : https://developer.apple.com/documentation/appstoreconnectapi

So far, it handles token generation / expiration, methods for listing resources and downloading reports. 

Please see [example.py](https://github.com/Ponytech/appstoreconnectapi/blob/master/example.py) on how to use the library and [api.py](https://github.com/Ponytech/appstoreconnectapi/blob/master/appstoreconnect/api.py#L58) for a list of available functions. This is a work in progress, API is subject to change between versions.


TODO:

* [ ] handle POST, DELETE and PATCH requests
* [X] sales report
* [ ] allow to sort resources
* [ ] API documentation
* [ ] handle the new "Provisioning" section