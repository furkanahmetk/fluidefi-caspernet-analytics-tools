# Usage Overview


## Prerequisites
- Have [Docker](https://www.docker.com/) installed in your machine.
- Have `casper-aggregator` already run and published data.
- Access the data base and run the following queries to create the tables needed for this service:
```
-- BlockSummary table
CREATE TABLE block_summary (
    id SERIAL PRIMARY KEY,
    address VARCHAR(100) NOT NULL,
    block_timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    reserve0 DOUBLE PRECISION NOT NULL,
    reserve1 DOUBLE PRECISION NOT NULL,
    num_swaps_0 BIGINT NOT NULL,
    num_swaps_1 BIGINT NOT NULL,
    num_mints BIGINT NOT NULL,
    num_burns BIGINT NOT NULL,
    mints_0 DOUBLE PRECISION NOT NULL,
    mints_1 DOUBLE PRECISION NOT NULL,
    burns_0 DOUBLE PRECISION NOT NULL,
    burns_1 DOUBLE PRECISION NOT NULL,
    volume_0 DOUBLE PRECISION NOT NULL,
    volume_1 DOUBLE PRECISION NOT NULL,
    block_number INTEGER NOT NULL,
    total_supply NUMERIC(155, 0) NOT NULL,
    CONSTRAINT unique_block_summary UNIQUE ( block_number, address )
);

-- HourlyData table
create table hourly_data
(
    id                    serial primary key,
    address               varchar(100)             not null,
    open_timestamp_utc    timestamp with time zone not null,
    close_timestamp_utc   timestamp with time zone not null,
    close_reserves_0      double precision         not null,
    close_reserves_1      double precision         not null,
    num_swaps_0           bigint                   not null,
    num_swaps_1           bigint                   not null,
    num_mints             bigint                   not null,
    num_burns             bigint                   not null,
    mints_0               double precision         not null,
    mints_1               double precision         not null,
    burns_0               double precision         not null,
    burns_1               double precision         not null,
    volume_0              double precision         not null,
    volume_1              double precision         not null,
    max_block             integer                  not null,
    close_lp_token_supply numeric(155)             not null,
    constraint address_timestamp_unique
        unique (address, open_timestamp_utc, close_timestamp_utc)
);
```

## Actions to do
- clone repository: `git clone https://github.com/fluidefi/fluidefi-caspernet-analytics-tools.git`
- change the working directory: `cd fluidefi-caspernet-analytics-tools`
- rename the `.env.example` file to `.env`
- replace the envirnoment variable values (that you will find inside the `.env` file) with the credentials of the running data base.
- start the services: `docker-compose up`


## Check the results:

You can check the logs of the docker containers for insights regarding the services results, to do that run `docker-compose logs` (if you want the logs of only one service then just add the service name to the previous command - for example, to get the logs of the block_summarizer you have to run `docker-compose logs block_summarizer`).<br><br> 
To check the outputs of the services open your preferred database viewer and explore parsed information of the `hourly_data` and `block_summary` tables.


## Run the Hourly Summarizer for a specific range of time

To re-do the summarization of the hourly data set a value for the environment variable `FORCE_RECALCULATE_START_HOUR` that you will find inside `.env` file and then restart the `hourly_summarizer` service `docker-compose up --buid -d hourly_summarizer`. This will allow the service to re-run the summarization for that specific range of time (the range is FORCE_RECALCULATE_START_HOUR and FORCE_RECALCULATE_START_HOUR + 1 hour) once and then get back to the normal behavior (so you don't have to stop the service and re-run it again).