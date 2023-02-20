CREATE TABLE block_summary (
    id SERIAL PRIMARY KEY,
    address VARCHAR(100) NOT NULL,
    token0 VARCHAR(100) NOT NULL,
    token1 VARCHAR(100) NOT NULL,
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