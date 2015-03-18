import unittest
import boto.ec2

from classes.ec2server import Ec2Server

class TestEc2Server(unittest.TestCase):
    def setUp(self):
        self.ec2Object = Ec2Server()

    def testParameters(self):
        print "**** Testing Parameters:"
        self.assertEqual(type(self.ec2Object.imageId), str)
        self.assertEqual(type(self.ec2Object.sshuser), str)
        self.assertEqual(type(self.ec2Object.region), str)
        self.assertEqual(type(self.ec2Object.keyName), str)
        self.assertEqual(type(self.ec2Object.instanceType), str)
        self.assertEqual(type(self.ec2Object.instanceSize), str)
        self.assertEqual(type(self.ec2Object.puppetModules), list)
        self.assertEqual(type(self.ec2Object.webSGName), str)
        self.assertEqual(type(self.ec2Object.sshSGName), str)
        self.assertEqual(type(self.ec2Object.keyDir), str)
        self.assertEqual(type(self.ec2Object.puppetScriptPath), str)
        self.assertEqual(type(self.ec2Object.timeout), int)
                  
    def testCreateAndDelete(self):
        print "**** Testing Creation and Deletion of an Instance:"
        instance = self.ec2Object.createInstance()
        self.assertEqual(type(instance), boto.ec2.instance.Instance)
        self.assertEqual(self.ec2Object.terminateInstanceAndDeleteVolumes(instance), True)
        
    def testCreateShell(self):
        instance = self.ec2Object.createInstance()
        self.ec2Object.createPtyShell(instance)

if __name__ == '__main__':
    unittest.main()  