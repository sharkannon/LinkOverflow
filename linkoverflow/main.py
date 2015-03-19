#!/usr/bin/env python
"""Main Screipt for LinkOverflow
This script is designed to be executed on the command line to create EC2 Instances.

Author: Stephen Herd (sharkannon@gmail.com)

Example:
    $ python main.py -d -n 1 -s micro -f /tmp/test.zip

Parameters:
    -d, --debug: Specify if debug is enabled (not defined means it's not).. currently it doesn't do anything:)
    -n, --num_instances: Define the number of Instances to create.
    -s, --size: Define the size of the instance. These are AWS EC2 Sizes (micro, large etc.)
    -f, --file: Defins the application file to upload (Must be a ZIP at this time)
"""

import argparse
import os
from classes.ec2server import Ec2Server

def main():
    parser = argparse.ArgumentParser(description='LinkOverflow AWS EC2 Instance Creator')
    parser.add_argument('-d', '--debug', action='store_true' ,help='specify if debug (dev) is enabled')
    parser.add_argument('-n', '--num_instances', default=1, type=int, help='Number of instances (default: 1)')
    parser.add_argument('-s', '--size', default='micro', help='size of server (default: micro)')
    parser.add_argument('-f', '--file', help='location of app zip')
    args = parser.parse_args()
    
    count = 1
    instances = []

    if not os.path.isfile(os.path.expanduser(os.path.expandvars(args.file))): 
        print "File not found: " + args.file + ", please verify and try again."
        exit(1)
        
    server = Ec2Server(instanceSize=args.size, puppetModules=['stankevich-python', 'stahnma-epel', 'puppetlabs-apache', 'puppetlabs-firewall'])
    
    while count <= args.num_instances:    
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