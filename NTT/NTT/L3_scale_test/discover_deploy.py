#!/usr/bin/env python

"""
Description: This script is to initialize the L3/HA scale test deployment
Developer: gopal@onecloudinc.com
"""
import pdb
import os
from neutronclient.v2_0 import client
from credentials import get_credentials
from config import TENANT_BASE_INDEX, NETWORK_COUNT, \
    EXTERNAL_NETWORK, print_scale_test_config, DEPLOYMENT_ID, \
    ASR_HOST, ASR_USER, ASR_PASSWORD, ENABLE_ASR_VERIFICATION, TENANT_COUNT, \
    TENANT_NAME_PREFIX, TENANT_NAME, TENANT_CREATION, VM_COUNT
from tenants import create_tenant, discover_tenant
from networks import create_network
from vm_instances import discover_vm_on_network
from prettytable import PrettyTable
from asr import GetASRCmd

credentials = get_credentials()
neutron = client.Client(**credentials)

    
def print_tenant_info(tenant_data):
    
    x = PrettyTable(['Tenant Name', 'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 1
    for entry in tenant_data:
        x.add_row([entry['tenant_name'], entry['status']])
    return x

def print_discovered_tenant(tenant_data,router_data,test_data):
    pdb.set_trace()
    y=PrettyTable(['Tenant Name','Router Name','Network Name','Network CIDR'])
    y.padding_width=1
    for x in tenant_data:
        for z in router_data:
            for a in test_data:
           
                y.add_row([x['tenant_name'],z['router_name'],a['network_data']['network_name'],a['network_data']['network_cidr']])
    return y

def print_consolidated_count(test_count):
    pdb.set_trace()
    y=PrettyTable(['Tenant Count','Router Count','Network Count','VM Count'])
    y.padding_width=1
    for i in test_count:
        y.add_row([i['tenant_count'],i['router_count'],i['network_count']]) 
    return y
def print_router_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 1
    for entry in router_data:
        x.add_row([entry['tenant_name'], entry['router_name'],
                  entry['router_status']])
    return x


def print_network_info(test_data):
    y = PrettyTable(['Tenant Name', 'Network Name', 'Network CIDR',
                    'Vlan ID', 'Subnet Name', 'Status'])
    y.align["Tenant_Name"] = "l"   # Left align source tenant values
    y.padding_width = 1
    for entry in test_data:
        y.add_row([entry['network_data']['tenant_name'],
                  entry['network_data']['network_name'],
                  entry['network_data']['network_cidr'],
                  entry['network_data']['network_vlan_id'],
                  entry['network_data']['subnet_name'],
                  entry['network_data']['status']])
    return y


def print_instance_info(test_data):
     
    z = PrettyTable(['Tenant Name', 'Instance Name', 'Status'])
    z.align["Tenant Name"] = "l"   # Left align source tenant values
    z.padding_width = 1
    for data in test_data:
        for ins in data['instance_data']:
            z.add_row([data['network_data']['tenant_name'],
                      ins['instance_name'],
                      ins['status']])
    return z


    

def asr_router_vrf_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Router VRF Name',
                    'Interfaces', 'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 2
    for entry in router_data:
        interfaces = ', '.join(entry['router_detail']['interfaces'])
        x.add_row([entry['tenant_name'], entry['router_name'],
                  entry['router_detail']['vrfname'],
                  interfaces,
                  entry['router_detail']['status']])
    return x


def asr_ipnat_pool_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Router VRF Name',
                     'NAT Pool Name', 'Start IP', 'End IP', 'Netmask',
                     'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 2
    for entry in router_data:
        x.add_row([entry['tenant_name'], entry['router_name'],
                   entry['ipnatpool_data']['vrfname'],
                   entry['ipnatpool_data']['nat_pool_name'],
                   entry['ipnatpool_data']['start_ip'],
                   entry['ipnatpool_data']['end_ip'],
                   entry['ipnatpool_data']['netmask'],
                  entry['ipnatpool_data']['status']])
    return x


def asr_iproute_info(router_data):
    x = PrettyTable(['Tenant Name', 'Router Name', 'Router VRF Name',
                     'Prefix', 'Mask', 'Interface', 'Next Hop Address',
                     'Status'])
    x.align["Tenant Name"] = "l"   # Left align source tenant values
    x.padding_width = 2
    for entry in router_data:
        x.add_row([entry['tenant_name'], entry['router_name'],
                   entry['iproute_data']['vrfname'],
                   entry['iproute_data']['prefix'],
                   entry['iproute_data']['mask'],
                   entry['iproute_data']['interface'],
                   entry['iproute_data']['next_hop_address'],
                   entry['iproute_data']['status']])
    return x


def asr_network_vrf_info(router_data):
    y = PrettyTable(['Tenant Name', 'Router Name', 'Network Name',
                     'Interface VRF Name', 'Internet Address',
                     'Vlan ID', 'Interfaces Status', 'Status'])
    y.align["Tenant Name"] = "l"   # Left align source tenant values
    y.padding_width = 2
    for entry in router_data:
        for interface in entry['interface_data']:
            y.add_row([entry['tenant_name'], entry['router_name'],
                       entry['network_vlan'][interface['vlan_id']],
                       interface['interface_name'], interface['ip_address'],
                       interface['vlan_id'], interface['interface_status'],
                       interface['status']])
    return y


def asr_interface_nat_info(router_data):
    y = PrettyTable(['Tenant Name', 'Router Name', 'Network Name',
                     'Interface Vlan ID', 'Dynamic NAT Entry',
                     'Access-list Entry', 'Status'])
    y.align["Tenant Name"] = "l"   # Left align source tenant values
    y.padding_width = 2
    for entry in router_data:
        for interface in entry['nat_data']:
            y.add_row([entry['tenant_name'], entry['router_name'],
                       entry['network_vlan'][interface['vlan_id']],
                       interface['vlan_id'], interface['nat_entry'],
                       interface['access_list_entry'], interface['status']])
    return y


def main():
    """
    This method will initialize the scale test deployment based on the global \
    config parameters mentioned on config.py file and creates the router with \
    external gateway connectivity to public network.
    """

    tenant_data = []
    router_data = []
    test_data = []
    test_count={}
    if TENANT_CREATION == True:
        print "\n"
        print_scale_test_config()
        print "\n"
        pdb.set_trace()
        print "Starting Scale Test Deployment"
        index = TENANT_BASE_INDEX
        for i in range(1, TENANT_COUNT + 1):
            tenant_name = TENANT_NAME_PREFIX + '-' + str(index)
            index += 1
            try:
                tenant_data.append(create_tenant(tenant_name))
            except Exception as exc:
                print "Exception occured on Tenant Creation: %s" % (exc.message)
                pass
        test_count["tenant_count"]=len(tenant_data)
        for tenant in tenant_data:
            
            #test= {'count': {'tenant_count': len(tenant_data)}}
            #test_count.append(test)
            router_dict = {}
            prefix = tenant['tenant_name']
            router_name = prefix + '-router'
            router_dict['tenant_name'] = tenant['tenant_name']
            router_dict['router_name'] = router_name
            router_dict['network_vlan'] = {}
            router_dict['router_detail'] = {}
            router_dict['ipnatpool_data'] = {}
            router_dict['iproute_data'] = {}
            router_dict['interface_data'] = []
            router_dict['nat_data'] = []

            router = neutron.list_routers(name=EXTERNAL_NETWORK)['routers']
            if not router:
                router_info = neutron.create_router({'router': {
                    'name': router_name, 'tenant_id': tenant['tenant_id']}})
                router = router_info['router']
                status = True
            elif router[0]['tenant_id'] == tenant['tenant_id']:
                router = router[0]
                status = True
            else:
                router = {}
                status = False

        router_dict['router_status'] = status
        networks = neutron.list_networks(name=EXTERNAL_NETWORK)
        network_id = networks['networks'][0]['id']
        neutron.add_gateway_router(router['id'],
                                   {'network_id': network_id,
                                    'tenant_id': tenant['tenant_id']})
        router_id = router['id']
        print('   - Created Router %s' % router['name'])

        for i in range(1, NETWORK_COUNT + 1):
            network_index = str(i)
            network_cidr = str(i) + "." + str(i) + "." + str(i) + ".0/24"
            test_data.append(create_network(tenant, router,
                             network_index, network_cidr))
        network_vlan = {}
        for entry in test_data:
            network_vlan[str(entry['network_data']['network_vlan_id'])] = \
                entry['network_data']['network_name']
        router_dict['network_vlan'] = network_vlan

    else:
        print "\n"
        print "=" * 50
        print "Discovering Tenant Topology on Scale Test Deployment"
        print "=" * 50
        try:
            for i in range(len(TENANT_NAME)):
                tenant_name = TENANT_NAME[i]
                tenant_data.append(discover_tenant(tenant_name))
                #test= {'count': {'tenant_count': len(tenant_data)}}
                #test_count.append(test)
                test_count["tenant_count"]=len(tenant_data)
                for tenant in tenant_data:
                    router_dict = {}
                    prefix = tenant['tenant_name']
                    router_name = prefix + '-router'
                    router_dict['tenant_name'] = tenant['tenant_name']
                    router_dict['tenant_id'] = tenant['tenant_id']
                    router_dict['router_name'] = router_name
                    router_dict['network_vlan'] = {}
                    router_dict['router_detail'] = {}
                    router_dict['ipnatpool_data'] = {}
                    router_dict['iproute_data'] = {}
                    router_dict['interface_data'] = []
                    router_dict['nat_data'] = []
                pdb.set_trace()
                router = neutron.list_routers(name=router_name)['routers'][0]
                if router['tenant_id'] == tenant['tenant_id']:
                    print('   - Router %s Discovered' % router_name)
                    status = True
                else:
                    print('   - Router %s Not Found' % router_name)
                    status = False
                router_id = router['id']
                router_dict['router_status'] = status
                router_data.append(router_dict)
                #test1= {'count': {'router_count': len(router_data)}}
                #test_count.append(test1)  
                test_count["router_count"]=len(router_data)              
                for i in range(1, NETWORK_COUNT + 1):
                    network_index = str(i)
                    network_cidr = str(i) + "." + str(i) + "." + str(i) + ".0/24"
                    network_name = prefix + '-net-' + network_index
                    subnet_name = prefix + "-subnet-" + network_index
                    ins_data = [] 
                    networks = neutron.list_networks(name=network_name)['networks']
                    for i in range(len(networks)):
                        if networks[i]['tenant_id'] == tenant['tenant_id']:
                            network_id = networks[i]['id']
                            network_vlan = networks[i]['provider:segmentation_id']
                            print('   - Network %s Discovered' % network_name)
                            print('   - Network ID %s Discovered' % network_id)
                            print('   - VLAN ID %s Discovered' % network_vlan)
                            status = True
                            for j in range(1, VM_COUNT + 1):
                                vm_name = network_name + '-vm-' + str(j)
                                ins_data.append(discover_vm_on_network(tenant['tenant_name'], vm_name, network_id))
                        else:
                            print('   - Network %s Not Found' % network_name)
                            status = False
 
                    result = {'network_data': {'tenant_name': tenant['tenant_name'],
                                               'network_name': network_name,
                                               'network_cidr': network_cidr,
                                               'subnet_name': subnet_name,
                                               'network_id': network_id,
                                               'network_vlan_id': network_vlan,
                                               'status':status},
                              'instance_data': ins_data}
                    test_data.append(result)
                    test_count["network_count"]=test_data
        except Exception:
            print "\n"
            print('   - Tenant %s Not Found' % tenant_name)

    if ENABLE_ASR_VERIFICATION:
        vrf_router_id = router_id[:6]
        print vrf_router_id
        vrfname = "nrouter" + '-' + vrf_router_id + '-' + DEPLOYMENT_ID
        print vrf_name

        asr_verify_cmd = GetASRCmd(asr_host=ASR_HOST,
                                   asr_host_port=22,
                                   asr_user=ASR_USER,
                                   asr_password=ASR_PASSWORD,
                                   asr_slots=["0"])
        router_detail = {'vrfname': vrfname, 'interfaces': '',
                         'status': ''}
        ipnatpool_data = {'vrfname': vrfname, 'nat_pool_name': '',
                          'start_ip': '', 'end_ip': '', 'netmask': '',
                          'status': ''}
        iproute_data = {'vrfname': vrfname, 'prefix': '', 'mask': '',
                        'interface': '', 'next_hop_address': '',
                        'status': ''}
        interface_data = []
        nat_data = []
        try:
            router_detail = asr_verify_cmd.get_router_detail(vrfname)
            ipnatpool_data = asr_verify_cmd.get_ipnat_pool_detail(vrfname)
            iproute_data = asr_verify_cmd.get_iproute_detail(vrfname)
            for interface in router_detail['interfaces']:
                interface_data.append(
                    asr_verify_cmd.get_network_interface_detail(vrfname,
                                                                interface))
            for interface in interface_data:
                interfaceid = DEPLOYMENT_ID + '_' + interface['vlan_id']
                nat_data.append(
                    asr_verify_cmd.get_interface_nat_access_detail(
                        interface['vlan_id'], interfaceid))
            asr_report = True
        except Exception as exc:
            print "\n"
            print "[ERROR] Caught exception on ASR Verification : %s" % \
                (exc.message)
            print "\n"
            asr_report = False
        router_dict['router_detail'] = router_detail
        router_dict['ipnatpool_data'] = ipnatpool_data
        router_dict['iproute_data'] = iproute_data
        router_dict['interface_data'] = interface_data
        router_dict['nat_data'] = nat_data
        router_data.append(router_dict)

    print "\n"
    print "=" * 50
    print "Scale Test Discovery Completed"
    print "=" * 50
    
    print "*" * 80
    print "Scale Test Deployment OpenStack Report"
    print "*" * 80

    print "\n"
    print "           Tenant Discovery Results      "
    print print_tenant_info(tenant_data)
    print "\n"
    print "           Router Discovery Results      "
    print print_router_info(router_data)
    print "\n"
    print "                 Network Discovery Results      "
    print print_network_info(test_data)
    print "\n"
    
    print "            Instance Discovery Results      "
    print print_instance_info(test_data)
    print "\n"
    
    print "             Tenant Name, Router Name, Network Name       "
    print print_discovered_tenant(tenant_data,router_data,test_data)
    print "\n"

    print"              Overall Count of resources"     
    print print_consolidated_count(test_count)  

    if ENABLE_ASR_VERIFICATION and asr_report:
        print "           OpenStack-ASR Router VRF Verification Results      "
        print asr_router_vrf_info(router_data)
        print "\n"

        print "           OpenStack-ASR IP NAT Pool Verification Results     "
        print asr_ipnat_pool_info(router_data)
        print "\n"
        print "           OpenStack-ASR IP Route Verification Results        "
        print asr_iproute_info(router_data)
        print "\n"

        print "           OpenStack-ASR Network VRF Verification Results     "
        print asr_network_vrf_info(router_data)
        print "\n"

        print("           OpenStack-ASR Network Interface's Dynamic NAT & "
              "Access list Entry Verification Results              ")
        print asr_interface_nat_info(router_data)
        print "\n"


if __name__ == '__main__':
    main()
