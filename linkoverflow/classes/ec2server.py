import boto.ec2
import boto.manage.cmdshell
import time
import os

class Ec2Server(object): 
    """
    Attributes
    
    region          = 'us-west-2'
    defaultUser     = 'centos'
    imageId         = 'ami-c7d092f7'
    keyName         = 'linkoverflow'
    instanceType    = 't2'
    instanceSize    = 'micro'
    puppetModules   = ['stankevich-python', 'stahnma-epel', 'puppetlabs-mysql', 'puppetlabs-apache']
    webSGName       = 'linkoverflow-webserver-sg'
    sshSGName       = 'linkoverflow-ssh-sg'
    keyDir          = '~/.ssh')   
    
    """
    def __init__(self, 
                 region         = 'us-west-2', 
                 sshuser        = 'centos', 
                 imageId        = 'ami-c7d092f7', 
                 keyName        = 'linkoverflow', 
                 instanceType   = 't2', 
                 instanceSize   = 'micro',
                 puppetModules  = [],
                 webSGName      = 'linkoverflow-webserver-sg',
                 sshSGName      = 'linkoverflow-ssh-sg',        
                 keyDir         = '~/.ssh'):
        
        self.region         = region
        self.sshuser        = sshuser
        self.imageId        = imageId
        self.keyName        = keyName
        self.instanceType   = instanceType
        self.instanceSize   = instanceSize
        self.puppetModules  = puppetModules
        keyDir              = os.path.expandvars(keyDir)
        self.keyDir         = os.path.expanduser(keyDir)
        self.conn           = boto.ec2.connect_to_region(region)
        self.webSGName      = webSGName
        self.sshSGName      = sshSGName

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
    
    def _createKeyDir(self):
        keyDir = self.keyDir
        if not os.path.isdir(keyDir):
            os.mkdir(keyDir, 0700)
    
        open(os.path.join(keyDir, 'known_hosts'), 'a').close()
    
    def createInstance(self):
        conn = self.conn
        self._createKey()
        self._createSecurtiyGroup()
        
        res = conn.run_instances(
            self.imageId,
            key_name        = self.keyName,
            instance_type   = self.instanceType + '.' + self.instanceSize,
            security_groups = [self.webSGName, self.sshSGName])
        
        instance = res.instances[0]
        
        while instance.update() != "running":
            time.sleep(5)  # Run this in a green thread, ideally
        
        return instance

    def getInstance(self, instanceId):
        conn = self.conn
        try:
            res = conn.get_all_instances(instance_ids = instanceId)
        except conn.ResponseError, e:
            raise
        
        instance = res[0].instances[0]
        
        return instance
        

    def createPtyShell(self, instance):
        keyDir  = self.keyDir
        keyName = self.keyName
        user    = self.sshuser
        
        while instance.update() != "running":
            time.sleep(5)

        cmd = boto.manage.cmdshell.sshclient_from_instance(instance, os.path.join(keyDir, keyName + '.pem'), user_name=user)

        return cmd
    
    def uploadFile(self, instance, localSrc, remoteDest):
        cmd = self.createPtyShell(instance)
        print "Uploading " + os.path.basename(localSrc) + " to " + instance.ip_address  + "..."
        sftp = cmd.open_sftp()
        sftp.put(localSrc, remoteDest)
        
    def installPuppet(self, instance):
        print "Installing Puppet on "  + instance.ip_address + "..."
        cmd = self.createPtyShell(instance)
        channel1 = cmd.run_pty('sudo rpm -ivh http://yum.puppetlabs.com/puppetlabs-release-el-7.noarch.rpm')
        status1 = channel1.recv_exit_status()
        
        channel2 = cmd.run_pty('sudo yum install -y puppet facter')
        status2 = channel2.recv_exit_status()
        
        return status1, status2
        
    def installPuppetModules(self, instance, modules=[]):
        self.installPuppet(instance)
        
        if not modules:
            modules = self.puppetModules
        else:
            modules = self.puppetModules + modules
            
        for module in modules:
            print "Installing Puppet Module (" + module + ") on " + instance.ip_address  + "..."
            cmd = self.createPtyShell(instance)
            channel = cmd.run_pty('sudo /usr/bin/puppet module install ' + module)
            status = channel.recv_exit_status()
            
    def configEnvironment(self, instance, puppetScriptPath, puppetModules=[]):
        self.uploadFile(instance, puppetScriptPath, '/tmp/' + os.path.basename(puppetScriptPath))
        self.installPuppetModules(instance, puppetModules)
        
        print "Configuring Environment on "  + instance.ip_address + "..."
        
        cmd = self.createPtyShell(instance)
        channel = cmd.run_pty('sudo /usr/bin/puppet apply /tmp/' + os.path.basename(puppetScriptPath))
        status = channel.recv_exit_status()
        
        return status
