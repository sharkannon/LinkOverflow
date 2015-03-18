#LinkOverflow

##Requirements
* python 2.7.9 (tested)
* python-paramiko (1.12.4 tested)
* python-boto (2.25.0 tested)

##Assumptions
I've had to make some assumptions based on my understanding of how Django works and installs:

1. The application will be packaged in a .zip file called linkoverflow.zip. 
2. You created the site by using (Or use the same structure it generates):
```
django-admin.py startproject linkoverflow
```
3. You've zipped the package from the top folder (When you unpack the zip, you would find manage.py in the linkoverflow folder).
4. You are using sqlite vs postgres or mysql.

##Running the application
1. Check out the application
```
git clone https://github.com/sharkannon/LinkOverflow.git
```
2. Go to the "bin" directory.
```
cd LinkOverflow/bin
```
3. Execute:
```
launch <parameters to be defined>
```