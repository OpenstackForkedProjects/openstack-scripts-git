#!/usr/bin/env python
"""
Description: This script is to launching VMs on the network.
Developer: gopal@onecloudinc.com
"""

import os
import time
import pdb
import novaclient.v1_1.client as nvclient
from novaclient.base import *
from novaclient.exceptions import NotFound
from config import FLOATING_IP_CREATION, IMAGE_NAME, FLAVOUR_NAME,OS_USERNAME, OS_TENANT_NAME, OS_PASSWORD, OS_AUTH_URL
from credentials import get_nova_credentials, get_tenant_nova_credentials,get_credentials
from floating_ips import add_floating_ip_for_vm
import glanceclient.v2.client as glance_client
import keystoneclient.v2_0.client as ksclient
keystone = ksclient.Client(auth_url="http://172.168.2.40:35357/v2.0",
                           username="admin",
                           password="admin",
                           tenant_name="admin")
token = keystone.auth_ref['token']['id']

credentials = get_nova_credentials()
nova = nvclient.Client(**credentials)
#glance=glance_client.Client(username=OS_USERNAME,password=OS_PASSWORD,tenant_name=OS_TENANT_NAME,auth_url=OS_AUTH_URL)
glance=glance_client.Client(endpoint="http://172.168.2.40:9292", token=token)
 

if not nova.keypairs.findall(name="admin"):
    with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
        nova.keypairs.create(name="admin", public_key=fpubkey.read())

def upload_image_glance():
    #pdb.set_trace()
    image_list=glance.images.list()
    image_file="/home/onecloud/NTT/keerthi/ubuntu.img"
    image=glance.images.create(disk_format="qcow2",container_format="bare",name="ubuntu")
    print("image status %s"%(image.status))
    ss=glance.images.upload(image.id,open('/home/onecloud/NTT/keerthi/ubuntu.img','rb'))
    print("Current Image status <%s>"%(image.status))

    #with open(image_file) as img:
        #image=glance.images.create(name="ubuntu",disk_format="raw",container_format="bare",data=img)
        
        #print("Current Image status %s"%(image.status))
     

def launch_vm_on_network(tenant_name, vm_name, network_id):
    """
    This method is to launch VM on the given network & VM Name.
    """
    #pdb.set_trace()
    instance=None 
    tenant_credentials = get_tenant_nova_credentials(tenant_name)
    
    nova = nvclient.Client(**tenant_credentials)
    nova.quotas.update(tenant_name, instances=-1, cores=-1, ram=-1, fixed_ips=-1, floating_ips=-1)
    with open('user.txt') as userdata:
        user_data = userdata.read()
    try:
	image_list=nova.images.find(name="ubuntu")
    except NotFound:
	upload_image_glance()

    #for img in image:
        #if img.name == 'ubuntu':
            #print "image found"
    try:

        flavor = nova.flavors.find(name='traffic')
    except:
        flavor = nova.flavors.create(name="traffic",ram="2048",vcpus="1",disk="10")

      
    try:
        
        instance = nova.servers.create(name=vm_name, image=image_list,
                                       flavor=flavor,
                                       key_name="admin",
                                       nics=[{'net-id': network_id}],userdata=user_data)
    except Exception:
        pass

    # Poll at 15 second intervals, until the status is no longer 'BUILD'
    print "  * Instance <%s> created on network <%s>: "%(vm_name,str(network_id))
    status = instance.status
    while status == 'BUILD':
        time.sleep(15)
        # Retrieve the instance again so the status field updates
        instance = nova.servers.get(instance.id)
        status = instance.status

    print "   - Current status: %s" % status
    if FLOATING_IP_CREATION:
        add_floating_ip_for_vm(tenant_name, instance)

    ins_data = {'instance_name': vm_name, 'status': status}
    return ins_data

#def endpoint_discovery(tenant_data,network_data):

#    tenant_credentials = get_tenant_nova_credentials(tenant_name)
#    nova = nvclient.Client(**tenant_credentials)
#    instance_list = nova.servers.list()


def discover_vm_on_network(tenant_name):
    """
    This method is used to discover instances per tenant
    """
    name=None
    status=None
    try:
        tenant_credentials = get_tenant_nova_credentials(tenant_name)
        nova = nvclient.Client(**tenant_credentials)
        instance_list=nova.servers.list()
        #instance = nova.servers.find(name=vm_name)
        if instance_list > 0:
         
            for inst in instance_list:
            
                instance_id = inst.id
                name=inst.name
                inst_find=nova.servers.find(id=instance_id)
                print('   - Instance %s Discovered' % inst.name)
                print('   - Instance ID %s Discovered' % instance_id)
                print('   - Instance %s Status' % inst.status)
                status=inst.status
    except Exception:
        print('   - Instance Not Found')
        status = False

    ins_data = {'instance_name': name, 
                                'status': status }
    return ins_data


def terminate_vm_on_network(tenant_name, vm_name, network_id):
    """
    This method is to terminate VM on the given network & VM Name.
    """
    pdb.set_trace()  
    tenant_credentials = get_tenant_nova_credentials(tenant_name)
    nova = nvclient.Client(**tenant_credentials)
    nova.quotas.delete(tenant_name)
    try:
        instance = nova.servers.find(name=vm_name)
        nova.servers.delete(instance.id)
        print "  * Instance terminated on network: " + str(network_id)
    except Exception:
        print "  * Instance Not Found on network: " + str(network_id)
        pass
    return True
