from keystoneclient.v2_0 import client


OS_USERNAME = 'admin'
OS_TENANT_NAME = 'admin'
OS_PASSWORD = 'admin'
OS_AUTH_URL = 'http://172.168.2.40:5000/v2.0/'

keystone = client.Client(username=OS_USERNAME, password=OS_PASSWORD, auth_url=OS_AUTH_URL)
import pdb
pdb.set_trace()

tenants = keystone.tenants.list()
for tenant in tenants:
    print tenant.__dict__


