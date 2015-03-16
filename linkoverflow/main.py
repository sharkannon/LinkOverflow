from classes.ec2server import Ec2Server

server = Ec2Server()
instance = server.createInstance(puppetModules=['stankevich-python', 'stahnma-epel', 'puppetlabs-apache', 'puppetlabs-firewall'])

server.configEnvironment(instance, '../scripts/django.pp')