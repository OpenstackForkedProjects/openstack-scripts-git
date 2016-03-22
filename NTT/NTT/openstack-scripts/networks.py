#!/usr/bin/env python
"""
Description: This script is to create network, subnets, router with \
             external gateway mapping.
Developer: gopal@onecloudinc.com
"""
import pdb
import os
from neutronclient.v2_0 import client
from credentials import get_credentials
from config import NETWORK_COUNT, VM_COUNT, FLOATING_IP_CREATION
from vm_instances import launch_vm_on_network, terminate_vm_on_network
from floating_ips import release_all_floating_ips
from datetime import datetime, timedelta
from pytz import timezone

credentials = get_credentials()
neutron = client.Client(**credentials)
fmt = "%Y-%m-%d %H:%M:%S %Z%z"


def create_network(tenant, router, network_index, network_cidr):
    """
    This method is used to create network, subnets, interfaces on router with \
    external gateway mapping for the given network name and CIDR.
    """

    try:
        prefix = tenant['tenant_name']
        network_name = prefix + '-net-' + network_index
        print "\n"
        print "=" * 50
        print "   Initiated Network Creation for " + network_name
        print "=" * 50
        print "\n"

        body_sample = {'network': {'name': network_name,
                                   'tenant_id': tenant['tenant_id']}}
        start_time = datetime.now(timezone('US/Pacific'))
        try:
            net = neutron.create_network(body=body_sample)
            net_dict = net['network']
            network_id = net_dict['id']
            network_vlan = net_dict['provider:segmentation_id']
            print('   - Network %s created' % net_dict['name'])
            net_status = True
        except Exception:
            net_dict = {}
            net_status = False

        subnet_name = prefix + "-subnet-" + network_index
        try:
            tenant_id = tenant['tenant_id']
            body_create_subnet = {'subnets': [{'name': subnet_name,
                                               'cidr': network_cidr,
                                               'ip_version': 4,
                                               'network_id': network_id,
                                               'tenant_id': tenant_id}]}
            subnet_detail = neutron.create_subnet(body=body_create_subnet)
            subnet = subnet_detail['subnets'][0]
            print('   - Created subnet %s' % subnet['name'])
            net_status = True
        except Exception:
            subnet = {}
            net_status = False

        neutron.add_interface_router(router['id'], {'subnet_id': subnet['id'],
                                     'tenant_id': tenant['tenant_id']})
        print ('   - Created interface between %s' % subnet['name'])
    finally:
        print "\n"
        msg = "<== Completed Network Creation with External Gateway "
        msg += "Successfully ==>"
        print msg
        end_time = datetime.now(timezone('US/Pacific')) 
        print "\n"
        print "-"*65
        print ("    Network %s Creation Time Summary :" % network_name)
        print "-"*65
        print "\n"
        print('   - Test Started Time   :\t %s' % (start_time.strftime(fmt)))
        print('   - Test Ended Time     :\t %s' % (end_time.strftime(fmt)))

    print "\n"
    print "=" * 50
    print "   Initiated VM Deployment " + network_name
    print "=" * 50
    print "\n"

    ins_data = []
    for i in range(1, VM_COUNT + 1):
        vm_name = network_name + '-vm-' + str(i)
        start_time = datetime.now(timezone('US/Pacific'))
        ins_data.append(launch_vm_on_network(tenant['tenant_name'],
                        vm_name, network_id))
        end_time = datetime.now(timezone('US/Pacific'))

    print "\n"
    msg = "<== Completed VM Launch on Network with Floating IP Allocation "
    msg += "Successfully ==>"
    print msg
    print "\n"
    print "-"*65
    print ("    Instance %s Creation Time Summary :" % vm_name)
    print "-"*65
    print "\n"
    print('   - Test Started Time   :\t %s' % (start_time.strftime(fmt)))
    print('   - Test Ended Time     :\t %s' % (end_time.strftime(fmt)))

    result = {'network_data': {'tenant_name': tenant['tenant_name'],
                               'network_name': network_name,
                               'network_cidr': network_cidr,
                               'subnet_name': subnet_name,
                               'network_id': network_id,
                               'network_vlan_id': network_vlan,
                               'status': net_status},
              'instance_data': ins_data}
    return result


def delete_vm(tenant_data,network_data):
    """
    This method is used to delete vms, network, subnets, interfaces on router \
    with external gateway mapping for the given network name and CIDR.
    """
    pdb.set_trace()
    #prefix = tenant_name
    network_list = []
    router_list = []
    count=1
    #router_list.append(prefix + '-router')
    #for i in range(1, NETWORK_COUNT + 1):
        #network_list.append(prefix + '-net-' + str(i))
    for tenant in tenant_data:
        for network in network_data:
            vm_name=tenant['name'] + '-vm-' + str(count)
            if ((network['network_list']['tenant_name'] == tenant['name']) and (network['network_list']['shared'] == False)):
    
                
                terminate_vm_on_network(tenant['name'], vm_name,network['network_list']['network_id'])
                count += 1

    release_all_floating_ips()
def delete_networks(tenant_data,network_data):
    pdb.set_trace()   
    networks=None
    for tenant in tenant_data:
        networks=neutron.list_networks(tenant_id=tenant['id'])['networks']
        routers=neutron.list_routers(tenant_id=tenant['id'])['routers']
        subnets=neutron.list_subnets(tenant_id=tenant['id'])['subnets']
        
           
        for router in routers:
            ports=neutron.list_ports(tenant_id=tenant['id'])['ports']
            for port in ports:
                #for subnet in subnets:
                 if (port['device_id'] == router['id'] and port['device_owner'] == 'network:router_interface'):
                      neutron.remove_interface_router(router['id'],{'subnet_id':port['fixed_ips'][0]['subnet_id']})
                      neutron.remove_gateway_router(router['id'])
                      neutron.delete_network(port['network_id'])
            neutron.delete_router(router['id']) 
            #neutron.delete_network(network['id'])

    #for network in networks:
        #neutron.delete_network(network['id'])
                 
                        #for subnet in subnets:
                          #for network in networks:
    
                

                            

    #if FLOATING_IP_CREATION:
        #release_all_floating_ips()
        #print "\n"
        #print("<== Released all Floating IPs Successfully ==>")
    #return True
