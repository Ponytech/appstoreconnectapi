#!/usr/bin/env python

import sys
from appstoreconnect import Api, UserRole

if __name__ == "__main__":
    key_id = sys.argv[1]
    key_file = sys.argv[2]
    issuer_id = sys.argv[3]
    api = Api(key_id, key_file, issuer_id)

    # list all apps
    apps = api.list_apps()
    for app in apps:
        print(app.name, app.sku)

    # filter apps
    apps = api.list_apps(filters={'sku': 'DINORUSH', 'name': 'Dino Rush'})
    print("%d apps found" % len(apps))

    # modify a user
    user = api.list_users(filters={'username': 'finance@nemoidstudio.com'})[0]
    api.modify_user_account(user, roles=[UserRole.FINANCE, UserRole.APP_MANAGER, UserRole.ACCESS_TO_REPORTS])

    # download sales report
    api.download_sales_and_trends_reports(
        filters={'vendorNumber': '123456789', 'frequency': 'WEEKLY', 'reportDate': '2019-06-09'}, save_to='report.csv')

    # download finance report
    api.download_finance_reports(filters={'vendorNumber': '123456789', 'reportDate': '2019-06'}, save_to='finance.csv')
