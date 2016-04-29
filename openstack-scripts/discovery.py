import pdb
import subprocess

from netaddr import *
from neutronclient.v2_0 import client
import novaclient.v1_1.client as nvclient

from credentials import get_credentials,get_tenant_nova_credentials

from vm_instances import discover_vm_on_network,launch_vm_on_network,vm_endpoint_discovery
from networks import delete_networks,delete_vm
credentials = get_credentials()
neutron = client.Client(**credentials)
tenant_data=[]
router_data=[]
network_dict={}
network_data=[]

def tenant_discovery():
    pdb.set_trace()
    tenant_data = [{'id': u'79bb772c47c24744853824305c796ea7','name': u'admin'}]
    network_data=network_discovery(tenant_data)
    
#   discover_instance(tenant_data)
    #launch_instance(tenant_data,network_data)
    endpoints=endpoint_discovery(tenant_data,network_data)
    print endpoints
#   destroy_all(tenant_data,network_data)

def get_ip_range():

    ips=IPRange("1.1.1.0","1.1.1.254")
    return ips

def endpoint_discovery(tenant_data,network_data):
    pdb.set_trace()
    instance_list=[]
    endpoint_list=[]
    final_data=[]
     
    for tenant in tenant_data:
        print("Get router information")
        routers=get_router(tenant)
        ports=get_ports(tenant)
        instance_ports = get_instance_ports(ports)
        for router in routers:
            router_detail = {}
            router_detail['id'] = router['id']
            router_detail['ports'] = get_router_ports(router, ports)
            subnets = []
            instance_list = []
            for port in router_detail['ports']:
                 
                subnets.append(get_port_subnets(tenant, port))
                router_detail['subnets'] = subnets
                for subnet in router_detail['subnets']:
                    if subnet['id'] != '':
                        endpoint_detail = get_subnet_endpoints(tenant, instance_ports, subnet)
                        ip_list = []
                        subnet['instances'] = endpoint_detail
                        for entry in endpoint_detail:
                            server = get_instance_detail(tenant['name'],entry['device_id'])
                            if entry['device_id'] not in instance_list and \
                               server.status == 'ACTIVE':
                                ips=get_ip_range()
                                ip_list.append(entry['ip_address'])

                                ipset=IPSet(ip_list)
                                for ip in ips:
                                    if ip in ipset:
                                        print("instance %s found"%(entry['ip_address']))
                                        instance_list.append(entry['device_id'])
                                        endpoint_list.append({'endpoints': ip_list,'tenant_name':tenant['name'],'subnet':subnet})

    return endpoint_list

def get_instance_detail(tenant,instance):

    tenant_credentials = get_tenant_nova_credentials(tenant)
    nova = nvclient.Client(**tenant_credentials)
    return nova.servers.get(instance)

def get_router_ports(router,ports):

    router_port_list = []
    for port in ports:
        if (port['device_id'] == router['id'] and
                port['device_owner'] == 'network:router_interface'):
            router_port_list.append(port)
    return router_port_list

def get_port_subnets(tenant,port):

    subnet = get_subnet_detail(tenant, port['fixed_ips'][0]['subnet_id'])['subnet']
    return {'id': port['fixed_ips'][0]['subnet_id'], 'name': subnet['name'],
            'ip_address': port['fixed_ips'][0]['ip_address'],'allocation_pool':subnet['allocation_pools']}

def get_subnet_detail(tenant, subnet):
    
    return neutron.show_subnet(subnet)

def get_subnet_endpoints(tenant,ports,subnet):

    endpoints = []
    for port in ports:
        endpoint_detail = {}
        if port['fixed_ips'][0]['subnet_id'] == subnet['id']:
            device_id = port['device_id'].encode('unicode_escape')
            ip = port['fixed_ips'][0]['ip_address'].encode('unicode_escape')
            endpoint_detail['device_id'] = device_id
            endpoint_detail['ip_address'] = ip
            endpoints.append(endpoint_detail)
    return endpoints


def get_router(tenant):
    routers=neutron.list_routers(tenant_id=tenant['id'])['routers']
    return routers
def get_ports(tenant):
    ports=neutron.list_ports(tenant_id=tenant['id'])['ports']
    return ports

def get_instance_ports(ports):
    pdb.set_trace()
    instance_port_list = []
    for port in ports:
        if port['device_owner'] == 'compute:nova' or port['device_owner'] == 'compute:compute' :
            instance_port_list.append(port)
    return instance_port_list

def destroy_all(tenant_data,network_data):

    delete_vm(tenant_data,network_data)
    delete_networks(tenant_data,network_data)
    
def network_discovery(tenant_data):
    pdb.set_trace()
    network_detail=[]
    subnet_detail=[]
    instance_list=[]
    net_sub={}
    for tenant in tenant_data:
        
        networks=neutron.list_networks(tenant_id=tenant['id'])['networks']


# List all subnets under each network and the tenants
        for net in networks:
            nets={}
            if net['tenant_id'] == tenant['id']:
                nets={'network_list':{'tenant_name':tenant['name'],
                                      'network_name':net['name'],'network_id':net['id'],'shared':net['shared'],'subnets':net['subnets']}}
                subnets=neutron.list_subnets(network_id=net['id'])['subnets']
                for subnet in subnets:
                    #net_sub={'networks':{'tenant_name':tenant['name'],'network_name':net['name'],'network_id':net['id'],'shared':net['shared']},'subnets':{'subnet_name':subnet['name'],'cidr':subnet['cidr']}}
                    net_sub={'networks':{'tenant_name':tenant['name'],'network_name':net['name'],'network_id':net['id'],'shared':net['shared'],'subnet_name':subnet['name'],'cidr':subnet['cidr']}}

                    subnet_detail.append(net_sub)
                    print "\n"
                    print "List subnets along with network details"
                    print "tenant name %s"%(tenant['name'])
                    print "network_name %s"%(net['name'])
                    print "subnet_name %s"%(subnet['name'])
                    print "cidr\t %s"%(subnet['cidr'])
                    print "allocation pools...%s"%(subnet['allocation_pools'])
                    print "\n"

                network_detail.append(nets)

    return network_detail
        
def launch_instance(tenant_data,network_data):
    #pdb.set_trace()
    inst_data=[]
    count=1
    for tenant in tenant_data:
        
        for network in network_data:
            pdb.set_trace()
            vm_name=tenant['name'] + '-vm-' + str(count)
            if ((network['network_list']['tenant_name'] == tenant['name']) and (network['network_list']['shared'] == True)):
                
                inst_data.append(launch_vm_on_network(tenant['name'],vm_name,network['network_list']['network_id']))

                count += 1

def discover_instance(tenant_data):
    instance_detail=[]
    pdb.set_trace()
    for tenant in tenant_data:
        
        vm_dict={}
        instance_detail.append(discover_vm_on_network(tenant['name']))
    print instance_detail     
        
        
def router_discovery(tenant_data):
    #pdb.set_trace()
    for tenant in tenant_data:
        #router_dict = {}
        router=neutron.list_routers(tenant_id=tenant['id'])['routers']
        for route in router:

            router_dict={}
            #for rout in router:
            
            if  route['tenant_id'] == tenant['id']:
                print('   - Router %s Discovered' % route['name'])
                status = True
                router_id = route['id']
                router_dict['tenant_name']=tenant["name"]
                router_dict['router_status'] = status
                router_dict['router_name']=route['name']
                router_data.append(router_dict)

            else:
                print("Tenant %s  not having any router"%(tenant['name']))  
            #if rout['tenant_id'] == tenant['id']:
                #print('   - Router %s Discovered' % rout['name'])
                #status = True
                #router_id = rout['id']
                #router_dict['tenant_name']=tenant["name"]
                #router_dict['router_status'] = status
                #router_dict['router_name']=rout['name']

        else:
            print('   - Router Not Found in %s tenant' % tenant['name'])
            status = False
        #router_id = rout['id']
        #router_dict['router_status'] = status
        #router_data.append(router_dict)

       
        #router_id = router['id']
        #router_dict['router_status'] = status
        #router_data.append(router_dict)
       
    print router_data    

def main():

    tenant_discovery()   







if __name__  == '__main__':

    main()
