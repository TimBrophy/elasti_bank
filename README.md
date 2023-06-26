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

## data commands
I'll be back to add this in a couple days. Got work to do.
