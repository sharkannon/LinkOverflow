#!/usr/bin/python
#
# Project: LinkOverflow test for xMatters
# Author: Stephen W. Herd
# Email: sharkannon@gmail.com

import boto.ec2
import time
import paramiko
import socket

region       = 'us-west-2'
defaultUser  = 'centos'
imageId      = 'ami-c7d092f7'
key          = 'xmatters'
instanceType = 't2.micro'

def createInstance():
    conn = boto.ec2.connect_to_region(region)
    
    res = conn.run_instances(
        imageId,
        key_name        = key,
        instance_type   = instanceType,
        security_groups = ['default'])
    
    instance = res.instances[0]
    
    while instance.update() != "running":
        time.sleep(5)

    return instance.ip_address

def testSSH(ipaddress):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    return sock.connect_ex((ipaddress,22))

def installPuppet(ipaddress):
    print "Connecting to: " + ipaddress + "... please wait..."
    while testSSH(ipaddress) != 0:
        time.sleep(5)

    print "Installing Puppet..."
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ipaddress, username=defaultUser, key_filename='xmatters.pem')

    (stdin1, stdout1, stderr1) = client.exec_command('sudo rpm -ivh http://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm',get_pty=True)

    (stdin2, stdout2, stderr2) = client.exec_command('sudo yum install -y puppet facter', get_pty=True)    
    
installPuppet(createInstance())
