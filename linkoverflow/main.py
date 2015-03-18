#!/usr/bin/env python

import argparse
from classes.ec2server import Ec2Server

def main():
    parser = argparse.ArgumentParser(description='LinkOverflow AWS EC2 Instance Creator')
    parser.add_argument('-e', '--environment', default='dev' ,help='specify the environment type (default: dev)')
    #parser.add_argument('-n', '--num_servers', default=1, type=int, metavar='1', nargs='1', help='Number of servers (default: 1')
    args = parser.parse_args()
    
    server = Ec2Server(puppetModules=['stankevich-python', 'stahnma-epel', 'puppetlabs-apache', 'puppetlabs-firewall'])
    instance = server.createInstance()
        
    server.configEnvironment(instance, '../scripts/django.pp')


if __name__ == '__main__':
    main()  