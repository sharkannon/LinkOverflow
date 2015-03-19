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
from threading import Thread
import Queue

from classes.ec2server import Ec2Server

def createNewInstance(args, q):
    server = Ec2Server(instanceSize=args.size, puppetModules=['stankevich-python', 'stahnma-epel', 'puppetlabs-apache', 'puppetlabs-firewall'])
    instance = server.createInstance()
    q.put(instance)
    
    server.installApplication(instance, args.file)
    q.task_done()

def main():
    parser = argparse.ArgumentParser(description='LinkOverflow AWS EC2 Instance Creator')
    reqGroup = parser.add_argument_group('required arguments')
    parser.add_argument('-d', '--debug', action='store_true' ,help='specify if debug (dev) is enabled')
    parser.add_argument('-n', '--num_instances', default=1, type=int, help='Number of instances (default: 1)')
    parser.add_argument('-s', '--size', default='micro', help='size of server (default: micro)')
    reqGroup.add_argument('-f', '--file', required=True, help='location of app zip')
    args = parser.parse_args()
    
    if not os.path.isfile(os.path.expanduser(os.path.expandvars(args.file))): 
        print "File not found: " + args.file + ", please verify and try again."
        exit(1)
    
    count = 1
    threads = []
            
    # Create num_instances number of instances
    q = Queue.Queue()
    
    # Create threads for each instances based on num_instances
    while count <= args.num_instances:
        threads.append(Thread(target=createNewInstance, args=(args,q)))
        count = count + 1
        
    # Start the threads
    for thread in threads:
        thread.start()
    
    instances = []
    
    # Wait for threds to finish and append results into the instances List
    for thread in threads:
        thread.join()
        instances.append(q.get())

    print "Exiting Start"
    
    print "**************************************"
    print "LinkOverflow Environments:"
    print "**************************************"
    for i in instances:
        print "Instance ID: " + i.id
        print "Instance IP: " + i.ip_address
        print "Username: centos"
        print "Environment: Development" if args.debug else "Environment: Production"
        print "URL: http://" + i.ip_address
        print "**************************************"
        
    print "SSH Key is found at: ~/.ssh/linkoverflow.pem. Please save this file or in the future you won't be able to log in to the instances you have created."

if __name__ == '__main__':
    main()
