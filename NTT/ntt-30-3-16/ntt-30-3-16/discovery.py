import pdb
from neutronclient.v2_0 import client
import novaclient.v1_1.client as nvclient

from credentials import get_credentials,get_tenant_nova_credentials
from config import TENANT_BASE_INDEX, NETWORK_COUNT, \
    EXTERNAL_NETWORK, print_scale_test_config, DEPLOYMENT_ID, \
    ASR_HOST, ASR_USER, ASR_PASSWORD, ENABLE_ASR_VERIFICATION, TENANT_COUNT, \
    TENANT_NAME_PREFIX, TENANT_NAME, TENANT_CREATION, VM_COUNT
from tenants import create_tenant, discover_tenant
from vm_instances import discover_vm_on_network,launch_vm_on_network,vm_endpoint_discovery
from networks import delete_networks,delete_vm
credentials = get_credentials()
neutron = client.Client(**credentials)
tenant_data=[]
router_data=[]
network_dict={}

def tenant_discovery():
    pdb.set_trace() 
    #for i in range(len(TENANT_NAME)):
    #tenant_name = TENANT_NAME[i]
    #tenant_data.append(discover_tenant())
    #discover_tenant()  
    tenant_data= [
               {'id': u'2931fbe17e8445da875bb915a29d0bbf', 'name': u'admin'},
               {'id': u'2e93f5f662974b1284e8be13dd472e48', 'name': u'demo'},
               {'id': u'ae9e7941b6764accae72a99662c189a5', 'name': u'tenant-test-101'},
               {'id': u'be0e4b8dc7754668b0e3d57e4f7f6f66', 'name': u'tenant-test-102'}]
               #{'id': u'fbb4907f073d4b5881a85c1692ae027a', 'name': u'services'}]
    #for i in range(len(tenant_data)):
        #print tenant_data[i]
    
#    router_discovery(tenant_data)
    network_data=network_discovery(tenant_data)            #List all subnets under each network from each tenant
    
    #discover_instance(tenant_data)
    #launch_instance(tenant_data,network_data)
    endpoints=endpoint_discovery(tenant_data,network_data)
    print endpoints
#    print tenant_data
#   print len(tenant_data)
#   destroy_all(tenant_data,network_data)


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
                                instance_list.append(entry['device_id'])
                                ip_list.append(entry['ip_address'])
                                endpoint_list.append({'endpoints': ip_list,'tenant_name':tenant['name'],'subnet':subnet})
                                

                   
                    

        #print "tenant_name..%s"%(tenant['name'])
        #print  "routers...%s"%(routers)
        #print "instance_ports....%s"%(instance_ports)
        #for ins in instance_ports:
            #pdb.set_trace() 
            #instances={'instance_detail':{'fixed_ip':ins['fixed_ips']}}       # list all instance fixed ips 
            #instance_list.append(instances)
    #return instance_list    
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
        if port['device_owner'] == 'compute:compute':
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

		    #routers=get_router(tenant)
                    #ports=get_ports(tenant)
                    #instance_ports = get_instance_ports(ports)
                    #for ins in instance_ports:
                        #pdb.set_trace()
                        #instances={'instance_detail':{'fixed_ip':ins['fixed_ips']}}
                        #instance_list.append(instances)
                    
                    #vm_endpoint_discovery(tenant['name'])

                    


            #subnets = net.get("subnets")       
	    #subnet_list = neutron.list_subnets(id=subnets)
	    #print subnet_list.get("subnets", [])[0].get("cidr")
                network_detail.append(nets)

        #pdb.set_trace()
        # subnets=neutron.list_subnets(tenant_id=tenant['id'])['subnets']
        # for subnet in subnets:
        #
        #     print "\n\n"
        #     print "tenant name %s"%(tenant['name'])
        #     print "network_id %s"%(subnet['network_id'])
        #
        #     print "subnet_id %s"%(subnet['id'])
        #     print "cidr\t %s"%(subnet['cidr'])
    #network_dict['network_list']=network_detail
    
    return network_detail
        
def launch_instance(tenant_data,network_data):
    #pdb.set_trace()
    inst_data=[]
    count=1
    for tenant in tenant_data:
        
        for network in network_data:
            pdb.set_trace()
            vm_name=tenant['name'] + '-vm-' + str(count)
            if ((network['network_list']['tenant_name'] == tenant['name']) and (network['network_list']['shared'] == False)):
                
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
