import logging
import pprint
from  novaclient import client as novclient
from  neutronclient.v2_0 import client as nclient
import time
import pdb
import MySQLdb
from keystoneclient.v2_0 import client as kclient
def main():
    net_list=['NET-A','NET-B','NET-C']
    ext_net_list=['EXT-NET-A','EXT-NET-B']
    ext_subnet_list=[]
    flavor_list={}
    
    router_list=['Router-A','Router-B']
    subnet_list={'subnets':[{'name':'Subnet-A','network_id':'','ip_version':4,'cidr':'1.1.1.0/24'},{'name':'Subnet-B','network_id':'','ip_version':4,'cidr':'2.2.2.0/24'}]}
    count = 0
    instance_detail={}
    networks={}
    logging.basicConfig(level=logging.INFO)
    logger=logging.getLogger(__name__)
    logger.info("Keystone authentication started....")
    time.sleep(5)
    logger.info("Wait for 5 seconds...")
    logger.info("done")
    neutr=nclient.Client(username='admin',password='admin',tenant_name='admin',auth_url='http://192.168.1.12:5000/v2.0/')
    novactr=novclient.Client('2',username='admin',api_key='admin',project_id='admin',auth_url='http://192.168.1.12:5000/v2.0/')
    logger.info("Authentication success...")
    #logger.info("getting input from user....")
    #network_count=int(raw_input("Enter the no of network to created >>\t"))
    #ext_network_count=int(raw_input("Enter the no of External network to be created >> \t"))
    #instance_detail['name']=raw_input("Please provide name for instance")
    #flavor_id=int(raw_input("Provide the flavor for the instance"))
    #netw=neutr.list_networks()
    #print netw
    #ss=db_connection(flavor_list,novactr)
    #us=ss.get(flavor_id)
    #if us:
        #logger.info("You choose %s flavor"%(us))
    #else:
        #logger.info("The flavor u choose is doesn't exists..")
        #exit
    #create_network(neutr,network_count,logger,net_list,count,subnet_list,novactr,flavor_id)
    delete_network(neutr,novactr,logger,net_list,subnet_list) 
    
def create_network(neutr,network_count,logger,net_list,count,subnet_list,novactr,flavor_id):
    pdb.set_trace()
    logger.info("Start creating external network ")
    ext_network=neutr.create_network({'network':{'name':'EXT-NET','admin_state_up':'True','router:external':'True'}})
    ext_id=ext_network['network']['id']
    vm_list=['vm-1','vm-2']
    logger.info("Creating external network subnet...")
    ext_subnet=neutr.create_subnet({'subnet':{'name':'EXT_subnet','network_id':ext_id,'ip_version':4,'cidr':'6.6.8.8/24'}})
    time.sleep(2)
    logger.info("creating router")
    router1=neutr.create_router({'router':{'name':'Router-1','admin_state_up':'True'}})
    router_id=router1['router']['id']
    neutr.add_gateway_router(router_id,{'network_id':ext_id})
    
    while count < network_count:

        neut=neutr.create_network({'network':{'name':net_list[count],'admin_state_up':'True'}})
        if  neut:
            net_id=neut['network']['id']
            logger.info("Network %s sucessfully created.."%(net_list[count]))
            time.sleep(4)
            logger.info("Start creating subnets")
            #nsub=neutr.create_subnet({'subnet':subnet_list['subnets'][count]})
            nsub=neutr.create_subnet({'subnet':{'name':subnet_list['subnets'][count]['name'],'network_id':net_id,'ip_version':subnet_list['subnets'][count]['ip_version'],'cidr':subnet_list['subnets'][count]['cidr']}})
            sub_id=nsub['subnet']['id']
            if nsub:
                logger.info("subnet is created for network %s"%(net_list[count]))
                time.sleep(4)
                logger.info("Adding interface to router")
                neutr.add_interface_router(router_id,{'subnet_id':sub_id})
                time.sleep(5)
                logger.info("Ready to launch the instances")
                pdb.set_trace()
                image = novactr.images.find(name="cirros")
                print net_id
                instance = novactr.servers.create(name=vm_list[count], image=image, flavor=flavor_id, nics=[{'net-id':net_id}])
                logger.info("Instance launched successfully on network %s"%(net_list[count]))
                time.sleep(4)            
                count = count+1
        else:
            logger.info("Error in network creation")
    time.sleep(3)	
    logger.info("setup is ready for testing..")

def db_connection(flavor_list,novactr):
    db=MySQLdb.connect(host="localhost",user="root",passwd="dafc1bce95654501",db="nova")
    cur=db.cursor()
    cur.execute("select id,name from instance_types")
    ss=novactr.networks.list()
    print ss
    return dict(cur.fetchall())

def delete_network(neutr,novactr,logger,net_list,subnet_list):
    logger.info("Start cleaning the dashboard")
    del_net={}
    server_delete(novactr,logger)
    delete_interface(neutr,logger)
    count=0

def server_delete(novactr,logger):
    #pdb.set_trace()
    logger.info("Fetching list of servers")
    myserver=novactr.servers.list()
    server_len=len(myserver)
    for i in range(server_len):
        ss=novactr.servers.delete(myserver[i])
        if ss:
            logger.info("Instances %s sucessfully deleted"%myserver[i])
        time.sleep(1)
def delete_interface(neutr,logger):
    
    mynetwork=neutr.list_networks()
    net_len=len(mynetwork['networks'])
    myrouter=neutr.list_routers()
    r_id=myrouter['routers'][0]['id']
    port_delete(neutr,logger,r_id)
    my_ports=neutr.list_ports()['ports']
    port_gateway=[]
    s=neutr.remove_gateway_router(r_id)
    if s:
        logger.info("gateway router is detached successful...")
        myrouter=neutr.list_routers()['routers']
        for r in range(len(myrouter)):
            
            neutr.delete_router(myrouter[r]['id'])
    logger.info("Deleting networks...")
    time.sleep(2)
    for j in range(net_len):
        dd=neutr.delete_network(mynetwork['networks'][j]['id'])

def port_delete(neutr,logger,r_id):
    logger.info("listing port details..")
    myports=neutr.list_ports()['ports']
    port_list=[]
    port_gateway=[]
    for port in myports:
       
        if (port['device_id'] == r_id and
                port['device_owner'] == 'network:router_interface'):
            port_list.append(port)
    logger.info("Removing router interfaces..")
    
    for i in range(len(port_list)):
 
        del_inf=neutr.remove_interface_router(r_id,{'subnet_id':port_list[i]['fixed_ips'][0]['subnet_id']})

#def get_id(novactr,logger):
    #welcome=novactr.servers.list(413fb5d3-c1bc-4267-80ab-6a27d0cfd04b)
    #print welcome
    
               
if __name__ == '__main__':
    main()
