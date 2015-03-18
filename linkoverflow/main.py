#!/usr/bin/env python

import argparse
from classes.ec2server import Ec2Server

def main():
    parser = argparse.ArgumentParser(description='LinkOverflow AWS EC2 Instance Creator')
    parser.add_argument('-e', '--environment', default='dev' ,help='specify the environment type (default: dev)')
    parser.add_argument('-n', '--num_servers', default=1, type=int, help='Number of servers (default: 1)')
    parser.add_argument('-s', '--size', default='micro', help='size of server (default: micro)')
    parser.add_argument('-f', '--file', help='location of app zip')
    args = parser.parse_args()
    
    count = 1
    instances = []

    while count <= args.num_servers:
        server = Ec2Server(instanceSize=args.size, puppetModules=['stankevich-python', 'stahnma-epel', 'puppetlabs-apache', 'puppetlabs-firewall'])
        instance = server.createInstance()
        server.installApplication(instance, args.file)
        instances.append(instance)
        count = count + 1
        
    print "**************************************"
    print "LinkOverflow Environments:"
    print "**************************************"
    for i in instances:
        print "Instance ID: " + i.id
        print "Instance IP: " + i.ip_address
        print "Username: centos"
        print "URL: http://" + i.ip_address
        print "**************************************"
        
    print "SSH Key is found at: ~/.ssh/linkoverflow.pem. Please save this file or in the future you won't be able to log in."

if __name__ == '__main__':
    main()