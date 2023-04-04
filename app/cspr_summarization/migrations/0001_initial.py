# Generated by Django 4.1.6 on 2023-02-28 14:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunSQL(
        """
            CREATE TABLE IF NOT EXISTS block_summary ( 
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
            CREATE TABLE IF NOT EXISTS hourly_data
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
                        unique (address, open_timestamp_utc, close_timestamp_utc),
                    CONSTRAINT different_values CHECK (open_timestamp_utc <> close_timestamp_utc)
            );
        """, 
        ),
    ]