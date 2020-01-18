## 0.5.1

Bugfixes:
 - Fixes token re-generation (@gsaraceno)

## 0.5.0

Features:
 -  Handle listing all resources in the provisioning section (devices thanks to @EricG-Personal)

## 0.4.1

Features:
 - Allow to query resources sorted
 - Allow passing key as a string value (@kpotehin)

Bugfixes:
 - Fixed sort param in reports (@kpotehin)

## 0.4.0

Features:
 - Handle fetching related resources (@WangYi)

Bugfixes:
 - When paging resources, fix missing resource in the first page (@WangYi)

## 0.3.0

Features:
  - Complete API rewrite, "list" methods return an iterator over resources, "get" method returns a resource 
  - Handles all GET endpoints (except the new "Provisioning" section)
  - Handle pagination
  - Handle downloading Finance and Sales reports

## 0.2.1

Bugfixes:

  - Cryptography dependency is required

## 0.2.0

Features:

  - Added more functions (@fehmitoumi)

## 0.1.0

Features:

  - Initial Release