from classes.ec2server import Ec2Server

server = Ec2Server()
#instance = server.createInstance(puppetModules=['stankevich-python', 'stahnma-epel', 'puppetlabs-apache', 'puppetlabs-firewall'])
instance = server.getInstance('i-615b926c')
server.terminateInstanceAndDeleteVolumes(instance)

#server.configEnvironment(instance, '../scripts/django.pp')