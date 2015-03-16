#!/usr/bin/python
#
# Project: LinkOverflow test for xMatters
# Author: Stephen W. Herd
# Email: sharkannon@gmail.com

import boto.ec2
import boto.manage.cmdshell
import time
import os

region          = 'us-west-2'

defaultUser     = 'centos'
imageId         = 'ami-c7d092f7'
keyName         = 'linkoverflow'
instanceType    = 't2'
puppetModules   = ['stankevich-python', 'stahnma-epel', 'puppetlabs-mysql', 'puppetlabs-apache']
webSGName       = 'linkoverflow-webserver-sg'
sshSGName       = 'linkoverflow-ssh-sg'
keyDir=os.path.expanduser('~/.ssh')

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
            key.save(keyDir)
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

def installPuppetLabsRPM(cmd):
    print "Installing PuppetLabs RPM..."
    channel = cmd.run_pty('sudo rpm -ivh http://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm')
    status = channel.recv_exit_status()  
    return status

def installPuppet(cmd):
    installPuppetLabsRPM(cmd)

    print "Installing Puppet..."
    channel = cmd.run_pty('sudo yum install -y puppet facter')
    status = channel.recv_exit_status()
    return status

def installPuppetModule(cmd, puppetModule):
    print "Installing Puppet Module(" + puppetModule + ")..."
    channel = cmd.run_pty('sudo puppet module install ' + puppetModule)
    status = channel.recv_exit_status()
    return status

def installPuppetModules(cmd):
    installPuppet(cmd)
    for puppetModule in puppetModules:
        installPuppetModule(cmd, puppetModule)

def uploadFile(cmd, localFile, remoteFile):
    sftp = cmd.open_sftp()
    sftp.put(localFile, remoteFile)
    sftp.close()
    
def configEnv(cmd):
    uploadFile(cmd, 'scripts/django.pp', '/tmp/django.pp')
    installPuppetModules(cmd)

    print "Configuring Environment..."
    channel = cmd.run_pty('sudo /usr/bin/puppet apply /tmp/django.pp')
    status = channel.recv_exit_status()
    return status

#def main()
instances = createInstance('micro', 1)
# Create .ssh dir and known_hosts file if they don't exist
if not os.path.isdir(keyDir):
    os.mkdir(keyDir, 0700)
    
open(os.path.join(keyDir, 'known_hosts'), 'a').close()

for instance in instances:
    while instance.update() != "running":
        time.sleep(5)
    
    cmd = boto.manage.cmdshell.sshclient_from_instance(instance, os.path.join(keyDir, keyName + '.pem'), user_name=defaultUser)
    configEnv(cmd)

