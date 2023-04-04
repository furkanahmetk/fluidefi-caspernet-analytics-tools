# Usage Overview


## Prerequisites
- Have [Docker](https://www.docker.com/) installed in your machine. <br>
Run these commands to check: `docker -v; docker compose version`.
```
Docker version 20.10.16, build aa7e414
docker compose version 1.29.2, build 5becea4c
```
- Have [`casper-aggregator`](https://github.com/fluidefi/fluidefi-caspernet-aggregator-tools) already run and published data. <br>
Open your preferred database viewer and explore that the different tables have data `blocks`, `block_hours`, `all_pairs` ... <br>

- As an alternative to the last point above (`have casper-aggregator already run`), you can just simply import the dump data (the output of the aggregator).<br>
To do that make sure to:
  1. Place the DB dump folder at the root level of the directory (at the same level where you have the `docker-compose.yml` file) - and make sure to rename the folder to `dump_data`.
  2. Copy configuration example to new file `cp .env.example .env`
  3. Replace the DB envirnoment variable values (that you will find inside the `.env` file) with the credentials of the running data base.
  4. Run this command to import the data `docker compose -f docker-compose.data-loader.yml up`.
  5. Once the step 4. above is done, all tables and data needed for the services should be populated. To check that open your DB with your prefered DB Viewer and check there that you've all tables.



## Actions to do
- Clone repository: `git clone https://github.com/fluidefi/fluidefi-caspernet-analytics-tools.git`
- Change the working directory: `cd fluidefi-caspernet-analytics-tools`
- Copy configuration example to new file `cp .env.example .env`
- Replace the envirnoment variable values (that you will find inside the `.env` file) with the credentials of the running data base.
- Build the common shared image (This step will speed up the build time of the services - build once and use it elsewhere): <br>
```
docker build  -f ./app/fluidefi-app.Dockerfile -t fluidefi-app  ./app
```
- Start the services: <br>
```
docker compose up
```
 This command will create the database tables needed on this service and then starts the services.
- Once the last step above is done then the app should be accessible at http://0.0.0.0:8080/ 


## Clean from previous runs
To cleanup containers, volumes and networks from previous runs, run this command: 
- `docker compose down --volumes`
After that remove the `.env` file, previously created, by running this command:
- `rm .env` 


## Check the results:

You can check the logs of the docker containers for insights regarding the services results, to do that run `docker compose logs` (if you want the logs of only one service then just add the service name to the previous command - for example, to get the logs of the block_summarizer you have to run `docker compose logs block_summarizer`).<br><br> 
To check the outputs of the services open your preferred database viewer and explore parsed information of the `hourly_data` and `block_summary` tables.


## Run the Hourly Summarizer for a specific range of time

To re-do the summarization of the hourly data set a value for the environment variable `FORCE_RECALCULATE_START_HOUR` that you will find inside `.env` file and then restart the `hourly_summarizer` service `docker compose up --buid -d hourly_summarizer`. This will allow the service to re-run the summarization for that specific range of time (the range is FORCE_RECALCULATE_START_HOUR and FORCE_RECALCULATE_START_HOUR + 1 hour) once and then get back to the normal behavior (so you don't have to stop the service and re-run it again).

<br><br>

# Run metrics computation services
In order to run the `data_server`, `exchange_rate_populator`, and `lp_summary_populator` services make sure to have the `.env` file at the root directory level as explained above [Prerequisites](#prerequisites) part. <br>
Then run the following commands: 
1. First we should build a common shared image between the services. This step will speed up the build time of the services (build once and use it elsewhere)<br>
```
docker build  -f ./app/data_servers/fluideFi-metrics.Dockerfile -t fluidefi-metrics ./app/data_servers 
```
2. Once the step 1 is done, we can start the services by running this command: <br>
```
docker compose -f ./app/data_servers/docker-compose.yml up  
```

## Clean from previous runs
To cleanup containers, volumes and networks from previous runs, run this command: 
- `docker compose -f ./app/data_servers/docker-compose.yml down --volumes`
After that remove the `.env` file, previously created, by running this command:
- `rm .env`