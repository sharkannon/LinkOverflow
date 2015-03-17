import unittest
import boto.ec2

from classes.ec2server import Ec2Server

class TestEc2Server(unittest.TestCase):
    def setUp(self):
        self.ec2Object = Ec2Server()

    def testDefaultValues(self):
        self.assertEqual(self.ec2Object.imageId, 'ami-c7d092f7')
        self.assertEqual(self.ec2Object.sshuser, 'centos')
        self.assertEqual(self.ec2Object.region, 'us-west-2')
  
    def testCreateObject(self):
        self.instance = self.ec2Object.createInstance()
        self.assertEqual(type(self.instance), boto.ec2.instance.Instance)
        self.ec2Object.terminateInstanceAndDeleteVolumes(self.instance)

if __name__ == '__main__':
    unittest.main()  