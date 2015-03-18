#LinkOverflow

##Requirements
* python 2.7.9 (tested)
* python-paramiko (1.12.4 tested)
* python-boto (2.25.0 tested)

##Assumptions
I've had to make some assumptions based on my understanding of how Django works and installs:

1. You are executing this on Linux (Though if you run main.py from "linkoverflow" it should work on Windows).
2. The Django application, that you want to install, will be packaged in a .zip file called linkoverflow.zip. 
3. You created the site by using (Or use the same structure it generates): 

    ```bash
    django-admin startproject linkoverflow
    ```
    
4. You've zipped the package from the top folder (When you unpack the zip, you would find manage.py in the linkoverflow folder).
5. You are using sqlite vs postgres or mysql.
6. You know how to install the dependencies.  If not, email me at sharkannon@gmail.com and I'll help you out.

##Credentials
To get your credentials, you'll have to log into your AWS account and get the AWS Access Key and Secret Access Key and provide them in a file like below:

1. Goto http://aws.amazon.com/console/
2. Sign in to AWS console
3. Goto "security_credential" (Top right corner of console) ===> Access Keys (Access Key ID and Secret Access Key)
4. Create a file `~/.aws/credentials`, on the machine you want to run this, that contains:

    ```
    [Credentials]
    aws_access_key_id = <your default access key>
    aws_secret_access_key = <your default secret key>
     ```
    
5. Execute (or add to .bash_profile) `export BOTO_CONFIG=~/.aws/credentials`

##Running the application
1. Check out the application: 

    ```bash
    git clone https://github.com/sharkannon/LinkOverflow.git
    ```

2. Go to the "bin" directory: 

    ```bash
    cd LinkOverflow/bin
    ```
    
3. Execute:

    ```bash
    sh launch -d -n <number of servers> -f <file/path of Django application zip> -s <size of server (micro, large etc.)>
    ```