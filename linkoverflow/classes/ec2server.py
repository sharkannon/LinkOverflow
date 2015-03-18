import boto.ec2
import boto.manage.cmdshell
import time
import os
from boto.beanstalk.response import Instance

class Ec2Server(object): 
    """
    Attributes
    
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
    timeout            = 120  
    """
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

        cmd = boto.manage.cmdshell.sshclient_from_instance(instance, os.path.join(keyDir, keyName + '.pem'), user_name=user)

        return cmd
    
    def _uploadFile(self, instance, localSrc, remoteDest):
        cmd = self.createPtyShell(instance)
        print "Uploading " + os.path.basename(localSrc) + " to " + instance.ip_address  + "..."
        localSrc = os.path.expandvars(localSrc)
        localSrc = os.path.expanduser(localSrc)
        
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
    