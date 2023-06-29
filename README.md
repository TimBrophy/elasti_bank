# elasti_bank
elasti_bank is a fictional, simulated online banking environment built to showcase how Elasticearch, and the turnkey Elastic Solutions: Enterprise Search, Observability & Security, can enable a unified view of key operational and business data, enabling greater data utility, efficiency and faster decision making.
## Setup
There are two aspects of the demo environment:
1) the elasti_bank simulated web app
2) the elasticsearch cluster with the relevant ingestion pipelines, ML models, dashboards and index mappings that make the solution function correctly.

At the moment, the source code for the application is house in this repo (the one you're looking at right now) and can be built from a machine image in the Elastic-SA project, but the Elasticsearch piece is available as a snapshot - although the process for distribution hasn't been figured out yet in this version.

## elasti_bank vm instance
1) login to the GCP console and make sure to choose 'elastic-sa' as your project;
2) go to 'Machine images' and look for the LATEST version of the elasti_bank image, which is named in the following format: timb-elastibank-demo-dd/mm/yyyy
3) create the VM and cd to the elasti_bank/config folder and update the .env file to point to your own Elasticsearch cluster by replacing the stored values in the following variables:
ES_CLOUD_ID_SECRET="<YOUR_CLOUD_ID>"
ES_PASS_SECRET="<YOUR_PASSWORD>"
ES_USER_SECRET="<YOUR_USER>"
APM_SECRET_TOKEN="<YOUR_APM_SECRET_TOKEN>"
APM_SERVER_URL="<YOUR_APM_SERVER_URL>"

5) make sure you also update the Google Maps secret details to your own credentials:
GOOGLE_MAPS_SECRET="<YOUR_SECRET_KEY>"

6) Because the IP address of the VM has changed, you will need to add the VM IP address to the nginx configuration:
   - sudo nano /etc/nginx/sites-available/elasti_bank
   - set "server_name <YOUR_VM_IP>;"

7) Because the chat part of the elasti_bank site is just a crowbar'd version of the esre python flask example, I've cheated a bit and simply spun that puppy up in a container locally and iframed it, so we need to head back to our elasti_bank/config/.env file and update the following variable:
   FLASK_APP_URL="http://<YOUR_VM_IP>:4000"

Lastly, make sure that all the services you need to be running in order to make this work are indeed running correctly:
1) sudo systemctl status gunicorn
2) sudo systemctl status nginx
3) sudo systemctl status postgresql
4) sudo systemctl status logstash

## bank chat setup
Check to see which containers are running (if any): 
sudo docker container ls

IF there are no containers at all, following the DOCKER instructions here to build one: 
https://github.com/TimBrophy/bank-faq-openai/tree/main/python-flask-example

Before running the Docker build and run commands, cd to 'bank-faq-openai/python-flask-example' otherwise the required manifests will not be found.

Just to clear the cache, please restart both gunicorn and nginx (in that order):
sudo systemctl restart gunicorn
sudo systemctl restart nginx

You should now find that your 'Chat' page loads correctly now. 

## data commands
In order to make use of a few management commands, it is necessary to start the Python virtual environment.
cd to the elasti_bank folder and pass the following command:
source venv/bin/activate

The virtual environment will start up and your terminal will now have '(venv)' as a prefix to your session.
You are now able to run the following built-in management commands:

Once you run a command DO NOT CLOSE THE TERMINAL. These currently require an active session in order to process. Fully aware how annoying this is. It's on the list of things that need to be improved. 

### working-data
command: python3 manage.py working-data

This command sets up all the basic working data for the project. Master data has been set up already as part of the VM image, but to get a fresh set of working data (users, bank accounts, transactions etc..) it is necessary to sun this command. 
Without this step, you risk having a disconnect between the Elastic cluster and the bank relational db data, or no data at all.

This command has one prompt, which ask whether you want to delete all users and start again. In almost all instances you want to do this. The only time you would say no is if you want to generate more data related to users.
This is a turnkey command. That is to say that it handles all local and remote operations such as deleting Elasticsearch indices and reapplying index templates.
This command generates 1000 users, and 3 months of data. 
All other commands in this app are modules of this overarching command and should only be used if you want to generate anything other than 1000 users and 3 months of financial data.

### real-time
command: python3 manage.py real-time #number_of_minutes(int)

Generates random transactions in 'real time' for random users. Pretends to be a real bank with transactions going through every few random seconds.  

### suggestions-generator
command: python3 manage.py suggestions-generator #number_of_months(int)

Generates random transactions that would trigger the recommendation engine on the home page. Basically queries the Special Offers table 
and creates transactions sprinkled through the number of months you specify so that it looks slightly more natural than dumping 5 transactions all together into the transaction history right now.

### generate-users
command: python3 manage.py generate-users #number_of_users(int)

This command generates random users at your request. It does not write it to the user log, which means data does not automatically get imported to Elasticsearch. 
Use this and all following commands only if you want to provide custom value for the input parameters of the data generated. 

### generate-bankaccounts
command: python3 manage.py generate-bankaccounts #number_of_months(int)

This command generates random bankaccounts for users at your request. It does not write it to the bankaccount log, which means data does not automatically get imported to Elasticsearch. 
Use this and all following commands only if you want to provide custom value for the input parameters of the data generated. 

### generate-transactions
command: python3 manage.py generate-transactions #number_of_months(int)

This command generates random transaction data at your request. It does not write it to the transaction log. 

### generate-activities
command: python3 manage.py generate-activities #number_of_months(int)

This command generates random interaction data at your request. It does not write it to the activity_data log. 

### export-to-json
command: python3 manage.py export-to-json

This command drops the contents of Postgres to 4 log files so that logstash picks them up and imports them into Elasticsearch. Small caveat: there's a bit of technical debt here in that I thought incorrectly that Logstash would handle
the duplication, but of course these are new log lines to Logstash imports them and you WILL get double records if you run this after the working data command. This command really should only be run in conjunction with a 'manual' setup where you dont use working data because you want more than 3 months of data. 


