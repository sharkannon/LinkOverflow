#!/usr/bin/python
#
# Project: LinkOverflow test for xMatters
# Author: Stephen W. Herd
# Email: sharkannon@gmail.com

import boto.ec2
import boto.manage.cmdshell
import time
import paramiko
import socket
import os

region          = 'us-west-2'

defaultUser     = 'centos'
imageId         = 'ami-c7d092f7'
keyName         = 'linkoverflow'
instanceType    = 't2'
puppetModules   = ['stankevich-python', 'stahnma-epel', 'puppetlabs-mysql', 'puppetlabs-apache']
webSGName       = 'linkoverflow-webserver-sg'
sshSGName       = 'linkoverflow-ssh-sg'


def createSecurityGroups(conn):
    print "Creating Security Group(s)...."
    try:
        web = conn.get_all_security_groups(groupnames=[webSGName])[0]
    except conn.ResponseError, e:
        if e.code == 'InvalidGroup.NotFound':
            web = conn.create_security_group(webSGName, 'LinkOverflow WebServer SG')
        else:
            raise
        
    try:
        web.authorize('tcp', 80, 80, '0.0.0.0/0')
    except conn.ResponseError, e:
        if e.code == 'InvalidPermission.Duplicate':  
            print 'Security Group: ' + webSGName +' already authorized'
        else:
            raise
        
    try:
        sshsg = conn.get_all_security_groups(groupnames=[sshSGName])[0]
    except conn.ResponseError, e:
        if e.code == 'InvalidGroup.NotFound':
            sshsg = conn.create_security_group(sshSGName, 'LinkOverflow SSH SG')
        else:
            raise
    
    try:
        sshsg.authorize('tcp', 22, 22, '0.0.0.0/0')
    except conn.ResponseError, e:
        if e.code == 'InvalidPermission.Duplicate':
            print 'Security Group: ' + sshSGName +' already authorized'
        else:
            raise

    
def createKey(conn):
    try:
        key = conn.get_all_key_pairs(keynames=[keyName])[0]
    except conn.ResponseError, e:
        print 'Creating SSH Keypair(' + keyName + ')...'
        if e.code == 'InvalidKeyPair.NotFound':
            key = conn.create_key_pair(keyName)
            key.save('.')
        else:
            raise
        
def createInstance(size = 'micro', numServers = 1):
    conn = boto.ec2.connect_to_region(region)
    
    createSecurityGroups(conn)
    createKey(conn)
    
    print "Creating Instance(s)...."
    res = conn.run_instances(
        imageId,
        max_count       = numServers,
        key_name        = keyName,
        instance_type   = instanceType + '.' + size,
        security_groups = [webSGName, sshSGName])
    
    return res.instances

def testSSH(ipaddress):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    return sock.connect_ex((ipaddress,22))

def createSSHClient(ipaddress, user):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ipaddress, username=user, key_filename=keyName + '.pem')
    return client

def installPuppetLabsRPM(ipaddress):
    print "Installing PuppetLabs RPM("+ ipaddress +")..."
    client = createSSHClient(ipaddress, defaultUser)
    (_stdin_, stdout, _stderr_) = client.exec_command('sudo rpm -ivh http://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm',get_pty=True)
    channel = stdout.channel
    status = channel.recv_exit_status()
    client.close()   
    return status

def installPuppet(ipaddress):
    installPuppetLabsRPM(ipaddress)

    print "Installing Puppet("+ ipaddress +")..."
    client = createSSHClient(ipaddress, defaultUser)
    (_stdin_, stdout, _stderr_) = client.exec_command('sudo yum install -y puppet facter', get_pty=True)
    channel = stdout.channel
    status = channel.recv_exit_status()
    client.close()
    return status

def installPuppetModule(ipaddress, puppetModule):
    print "Installing Puppet Module(" + puppetModule + ") on "+ ipaddress +"..."
    client = createSSHClient(ipaddress, defaultUser)
    (_stdin_, stdout, _stderr_) = client.exec_command('sudo puppet module install ' + puppetModule, get_pty=True)
    channel = stdout.channel
    status = channel.recv_exit_status()
    client.close()
    return status

def installPuppetModules(ipaddress):
    installPuppet(ipaddress)
    for puppetModule in puppetModules:
        installPuppetModule(ipaddress, puppetModule)

def uploadFile(ipaddress, localFile, remoteFile):
    client = createSSHClient(ipaddress, defaultUser)
    sftp = paramiko.SFTPClient.from_transport(client.get_transport())
    
    sftp.put(localFile, remoteFile)
    
    sftp.close()
    client.close()
    
def configEnv(ipaddress):
    uploadFile(ipaddress, 'scripts/django.pp', '/home/centos/django.pp')
    installPuppetModules(ipaddress)
    
    client = createSSHClient(ipaddress, defaultUser)
    print "Configuring Environment("+ ipaddress +")..."
    (_stdin, stdout, _stderr) = client.exec_command('sudo /usr/bin/puppet apply /home/centos/django.pp', get_pty=True)
    channel = stdout.channel
    status = channel.recv_exit_status()
    client.close()
    return status

instances = createInstance('micro', 1)

for instance in instances:
    while instance.update() != "running":
        time.sleep(5)
    
    #cmd = boto.manage.cmdshell.sshclient_from_instance(instance, keyName + '.pem', user_name=defaultUser)

    #cmd.open_sftp()
    
    print "Testing SSH Conectivity on " + instance.ip_address + ". Please wait..."
    
    while testSSH(instance.ip_address) != 0:
        time.sleep(5)
    
    configEnv(instance.ip_address)

