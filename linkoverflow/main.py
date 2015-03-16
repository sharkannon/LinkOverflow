from classes.ec2server import Ec2Server

server = Ec2Server()
instance = server.createInstance()

server.configEnvironment(instance, '../scripts/django.pp', ['stankevich-python', 'stahnma-epel', 'puppetlabs-apache', 'puppetlabs-firewall'])