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
    print "Creating Instance...."
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

def createSSHClient(ipaddress, user):
    print "Connecting to: " + ipaddress + "... please wait..."
    while testSSH(ipaddress) != 0:
        time.sleep(5)
        
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ipaddress, username=user, key_filename='xmatters.pem')
    return client

def installPuppetLabsRPM(ipaddress):
    print "Installing PuppetLabs RPM..."
    client = createSSHClient(ipaddress, defaultUser)
    (stdin, stdout, stderr) = client.exec_command('sudo rpm -ivh http://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm',get_pty=True)
    channel = stdout.channel
    status = channel.recv_exit_status()
    client.close()   
    return status

def installPuppet(ipaddress):
    installPuppetLabsRPM(ipaddress)

    print "Installing Puppet..."
    client = createSSHClient(ipaddress, defaultUser)
    (stdin, stdout, stderr) = client.exec_command('sudo yum install -y puppet facter', get_pty=True)
    channel = stdout.channel
    status = channel.recv_exit_status()
    client.close()
    
def uploadFile(ipaddress, localFile, remoteFile):
    client = createSSHClient(ipaddress, defaultUser)
    sftp = paramiko.SFTPClient.from_transport(client.get_transport())
    
    sftp.put(localFile, remoteFile)
    
    sftp.close()
    client.close()
    
def installDjango(ipaddress):
    uploadFile(ipaddress, 'scripts/django.pp', '/home/centos/django.pp')
    installPuppet(ipaddress)
    
    client = createSSHClient(ipaddress, defaultUser)
    print "Installing Django..."
    (stdin, stdout, stderr) = client.exec_command('sudo /usr/bin/puppet apply /home/centos/django.pp', get_pty=True)
    channel = stdout.channel
    status = channel.recv_exit_status()
    client.close()
    
installDjango(createInstance())
