"""Ec2Server Class
This class is designed to automate the creation of AWS EC2 Instnaces
and prepare them for application installs.  It ustilizes puppet to
configure the server and simple upload/unzip to install the application.

Author: Stephen Herd (sharkannon@gmail.com)

Example:
    from classes.ec2server import Ec2Server
    
    server = Ec2Server
    instance = server.createInstance()
    server.installApplication(instance, zipFileOfApplication)

Attributes:
    region (string): Defines the AWS Region the instance will be created on
    sshuser (string): Defines the application user used to log into the env (See the image's documentation)
    imageId (string): Defines the AWS Image used for the instance creation.
    keyName (string): The AWS EC2 KeyPair used to log into the box.  If it doesn't exist the class will create it. 
    instanceType (string): AWS EC2 Instance Type
    instanceSize (string): AWS EC2 Instance Size
    puppetModules (List of Strings): The PuppetForge modules to install on the server.
    webSGName (string): AWS EC2 Security Group used for Web access (Ports 80/443) 
    sshSGName (string): AWS EC2 Security Group used for SSH Access (Port 22)        
    keyDir (string): Path to where the SSH Key will be located/stored
    puppetScriptPath (string): Path to where the puppet config file is found.
    timeout (int): Timeout for for testing if the server has entered the correct status.
"""

import boto.ec2
import boto.manage.cmdshell
import paramiko
import time
import os

class Ec2Server(object): 
    def __init__(self, 
                 region             = 'us-west-2', 
                 sshuser            = 'centos', 
                 imageId            = 'ami-c7d092f7', 
                 keyName            = 'linkoverflow', 
                 instanceType       = 't2', 
                 instanceSize       = 'micro',
                 puppetModules      = [],
                 webSGName          = 'linkoverflow-webserver-sg',
                 sshSGName          = 'linkoverflow-ssh-sg',        
                 keyDir             = '~/.ssh',
                 puppetScriptPath   = '../scripts/linkoverflow.pp',
                 timeout            = 120):
        
        self.region             = region
        self.sshuser            = sshuser
        self.imageId            = imageId
        self.keyName            = keyName
        self.instanceType       = instanceType
        self.instanceSize       = instanceSize
        self.puppetModules      = puppetModules
        keyDir                  = os.path.expandvars(keyDir)
        self.keyDir             = os.path.expanduser(keyDir)
        self.conn               = boto.ec2.connect_to_region(region)
        self.webSGName          = webSGName
        self.sshSGName          = sshSGName
        self.timeout            = timeout
        self.puppetScriptPath   = puppetScriptPath

# Public Methods

    def createInstance(self):
        conn = self.conn
        self._createKey()
        self._createSecurtiyGroup()
        
        print "Creating instance..."
        res = conn.run_instances(
            self.imageId,
            key_name        = self.keyName,
            instance_type   = self.instanceType + '.' + self.instanceSize,
            security_groups = [self.webSGName, self.sshSGName])
        
        instance = res.instances[0]
        
        self._checkStatus('running', instance)
        
        return instance

    def terminateInstance(self, instance):
        if instance.update() != 'terminated':
            print "Terminating instance (" + instance.id + ")..."
            conn = self.conn
            try:
                conn.terminate_instances(instance_ids=[instance.id])
    
                self._checkStatus('terminated', instance)            
            except conn.ResponseError, e:
                raise
        else:
            print "Instance already terminated (" + instance.id + ")..."

    def terminateInstanceAndDeleteVolumes(self, instance):
        conn = self.conn
        
        try:
            volumes = conn.get_all_volumes(filters={'attachment.instance-id': instance.id})
        except conn.ResponseError, e:
            raise
        
        self.terminateInstance(instance)
        
        print "Deleting volumes associated with " + instance.id + "..."
        for volume in volumes:
            try:
                status = volume.delete()
            except conn.ResponseError, e:
                raise
        
        return status
        
    def getInstance(self, instanceId):
        conn = self.conn
        try:
            res = conn.get_all_instances(instance_ids = instanceId)
        except conn.ResponseError, e:
            if e.code == 'InvalidInstanceID.NotFound':
                print "Instance not found: " + instanceId
                exit(1)
            else:
                raise
        
        instance = res[0].instances[0]
        
        return instance
        

    def createPtyShell(self, instance):
        keyDir  = self.keyDir
        keyName = self.keyName
        user    = self.sshuser
        
        self._checkStatus('running', instance)
        
        try:
            cmd = boto.manage.cmdshell.sshclient_from_instance(instance, os.path.join(keyDir, keyName + '.pem'), user_name=user)
        except paramiko.ssh_exception.AuthenticationException:
            print "ERROR: SSH KeyPair validation failed.  Please do the following:"
            print "1. Retrieve the Private Key that is currently associated with the AWS KeyPair labeled: " + self.keyName + " (Hopefully you know who has it)."
            print "2. Copy it to: " + os.path.join(self.keyDir, self.keyName + '.pem')
            print "3. Rerun the application"
            print "**** OR ****"
            print "1. Login to the AWS Console and delete the AWS EC2 KeyPair labeled: " + self.keyName
            print "2. Remove (and backup) the license key from: " + os.path.join(self.keyDir, self.keyName + '.pem')
            print "3. Rerun the application"
            print "***************************************************************"
            print "**** NOTE: An Instance (" + instance.id + ") has already been created and has not been destroyed.  You may want to log into the AWS console and destroy it as they may not be useable."
            print ""

        return cmd

    def installPuppet(self, instance):
        print "Installing Puppet on "  + instance.ip_address + "..."
        cmd = self.createPtyShell(instance)
        channel1 = cmd.run_pty('sudo rpm -ivh http://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm')
        status1 = channel1.recv_exit_status()
        
        channel2 = cmd.run_pty('sudo yum install -y puppet facter')
        status2 = channel2.recv_exit_status()
        
        return status1, status2
        
    def installPuppetModules(self, instance):
        self.installPuppet(instance)
            
        for module in self.puppetModules:
            print "Installing Puppet Module (" + module + ") on " + instance.ip_address  + "..."
            cmd = self.createPtyShell(instance)
            channel = cmd.run_pty('sudo /usr/bin/puppet module install ' + module)
            status = channel.recv_exit_status()
            
    def configEnvironment(self, instance):
        self._uploadFile(instance, self.puppetScriptPath, '/tmp/' + os.path.basename(self.puppetScriptPath))
        self.installPuppetModules(instance)
        
        print "Configuring Environment on "  + instance.ip_address + "..."
        
        cmd = self.createPtyShell(instance)
        channel = cmd.run_pty('sudo /usr/bin/puppet apply /tmp/' + os.path.basename(self.puppetScriptPath))
        status = channel.recv_exit_status()
        
        return status
    
    def installApplication(self, instance, applicationPath):
        self._uploadFile(instance, applicationPath, '/tmp/'+ os.path.basename(applicationPath))
        self.configEnvironment(instance)
        
        cmd = self.createPtyShell(instance)
        channel = cmd.run_pty('sudo /usr/bin/unzip -o /tmp/' + os.path.basename(applicationPath) + ' -d /var/www/')
        status = channel.recv_exit_status()
        
        return status

# Private Methods

    def _createKey(self):
        self._createKeyDir()
        
        conn = self.conn
        keyName = self.keyName
        keyDir = self.keyDir
        
        try:
            key = conn.get_all_key_pairs(keynames=[keyName])[0]
        except conn.ResponseError, e:
            print 'Creating SSH Keypair(' + keyName + ')...'
            if e.code == 'InvalidKeyPair.NotFound':
                key = conn.create_key_pair(keyName)
                key.save(keyDir)
            else:
                raise
        
    def _createSecurtiyGroup(self):
        conn = self.conn
        webSGName = self.webSGName
        sshSGName = self.sshSGName
        
        try:
            web = conn.get_all_security_groups(groupnames=[webSGName])[0]
        except conn.ResponseError, e:
            if e.code == 'InvalidGroup.NotFound':
                web = conn.create_security_group(webSGName, self.keyName + webSGName)
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
                sshsg = conn.create_security_group(sshSGName, sshSGName)
            else:
                raise
        
        try:
            sshsg.authorize('tcp', 22, 22, '0.0.0.0/0')
        except conn.ResponseError, e:
            if e.code == 'InvalidPermission.Duplicate':
                print 'Security Group: ' + sshSGName +' already authorized'
            else:
                raise
    
    def _createKeyDir(self):
        keyDir = self.keyDir
        if not os.path.isdir(keyDir):
            os.mkdir(keyDir, 0700)
    
        open(os.path.join(keyDir, 'known_hosts'), 'a').close()
    
    def _checkStatus(self, status, instance):
        timeout = self.timeout
        start = now = time.time()
        
        while now - start < timeout:
            if instance.state == status:
                break
            
            time.sleep(5)
            
            try:
                instance.update()
            except boto.exception.EC2ResponseError, e:
                if e.code == 'InvalidInstanceID.NotFound':
                    print "Instance not found (" + instance.id + "), retrying..."
                else:
                    raise
            
            now = time.time()
    
    def _uploadFile(self, instance, localSrc, remoteDest):
        cmd = self.createPtyShell(instance)
        print "Uploading " + os.path.basename(localSrc) + " to " + instance.ip_address  + "..."
        localSrc = os.path.expandvars(localSrc)
        localSrc = os.path.expanduser(localSrc)
        
        if os.path.isfile(localSrc): 
            sftp = cmd.open_sftp()
            sftp.put(localSrc, remoteDest)
        else:
            print "File not found: " + localSrc + ", please verify and try again."
            exit(1)
            