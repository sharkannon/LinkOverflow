import boto.ec2
import time

region       = 'us-west-2'
defaultUser  = 'centos'
imageId      = 'ami-c7d092f7'
key          = 'test'
instanceType = 't2.micro'

def createInstance():
    conn = boto.ec2.connect_to_region(region)
    
    res = conn.run_instances(
        imageId,
        key_name        = key,
        instance_type   = instanceType,
        y_groups = ['default'])
    
    instance = res.instances[0]
    
    while instance.update() != "running":
        time.sleep(5)
    
    return instance.ip_address

