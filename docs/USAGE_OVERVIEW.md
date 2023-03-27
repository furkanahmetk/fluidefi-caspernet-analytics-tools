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
  1. Have the `dump_data.sql` file at the root level of the directory (at the same level where you have the `docker-compose.yml` file - and the filename should be `dump_data.sql`).
  2. run this command to import the data `docker compose -f docker-compose.data-loader.yml up`.



## Actions to do
- clone repository: `git clone https://github.com/fluidefi/fluidefi-caspernet-analytics-tools.git`
- change the working directory: `cd fluidefi-caspernet-analytics-tools`
- copy configuration example to new file `cp .env.example .env`
- replace the envirnoment variable values (that you will find inside the `.env` file) with the credentials of the running data base.
- start the services: `docker compose up`: This command will create the database tables needed on this service and then starts the services


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