from neutronclient.v2_0 import client as neutron_client



OS_USERNAME = 'admin'
OS_TENANT_NAME = 'admin'
OS_PASSWORD = 'admin'
OS_AUTH_URL = 'http://172.168.2.40:5000/v2.0/'
OS_TENANT_ID = '2931fbe17e8445da875bb915a29d0bbf'

def get_credentials():
    d = {}
    d['username'] = OS_USERNAME
    d['password'] = OS_PASSWORD
    d['auth_url'] = OS_AUTH_URL
    d['tenant_id'] = OS_TENANT_ID
    return d

tenants = [
	{'id': u'2931fbe17e8445da875bb915a29d0bbf', 'name': u'admin'}, 
	{'id': u'2e93f5f662974b1284e8be13dd472e48', 'name': u'demo'}, 
	{'id': u'ae9e7941b6764accae72a99662c189a5', 'name': u'tenant-test-101'}, 
	{'id': u'be0e4b8dc7754668b0e3d57e4f7f6f66', 'name': u'tenant-test-102'}, 
	{'id': u'fbb4907f073d4b5881a85c1692ae027a', 'name': u'services'}
]


credentials = get_credentials()
neutron = neutron_client.Client(**credentials)
netw = neutron.list_networks()
print netw
