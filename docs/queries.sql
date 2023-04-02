-- IMPORTANT NOTE: These SQL statements should be run on the aggregator database, not the analytics database

-- noinspection SqlNoDataSourceInspectionForFile

-- BlockSummary table
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

-- HourlyData table
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
        unique (address, open_timestamp_utc, close_timestamp_utc)
);
CREATE INDEX IF NOT EXISTS idx_lp_hourly_summary_address ON hourly_data ( address, open_timestamp_utc );
CREATE UNIQUE INDEX IF NOT EXISTS unq_lp_hourly_summary ON hourly_data ( open_timestamp_utc, close_timestamp_utc, address );

-- currency table
CREATE TABLE IF NOT EXISTS currency ( 
	id                              serial primary key,
	code                            varchar(3),
	symbol                          varchar(5),
	network_id                      integer,
	token_address                   varchar(100),
	display_name                    varchar(15),
	full_name                       varchar(100),
	html                            varchar(30),
	format                          varchar(10),
	active_fiat                     boolean                     DEFAULT false,
	decimals                        integer,
	token_type                      integer,
	collateral_currency_backed_by   integer,
	collateral_currency_pegged_to   integer,
	last_updated_utc                timestamp with time zone    DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT unq_currency_code    UNIQUE ( code ) 
 );

CREATE INDEX IF NOT EXISTS idx_currency_display_name ON currency  ( display_name );
CREATE INDEX IF NOT EXISTS idx_currency ON currency  ( token_address );
CREATE UNIQUE INDEX IF NOT EXISTS unq_currency_token_network ON currency ( token_address, network_id );
CREATE INDEX IF NOT EXISTS idx_currency_active_fiat ON currency  ( active_fiat );
ALTER TABLE currency ADD CONSTRAINT fk_collateral_currency_currency_id FOREIGN KEY ( collateral_currency_backed_by ) REFERENCES currency( id );

COMMENT ON TABLE  currency IS 'ISO 4217 three letter code of the currency. A current can be fiat or certain digital assets such at Ethereum and Bitcoin';
COMMENT ON COLUMN currency.code IS 'Three letter currency code';
COMMENT ON COLUMN currency.symbol IS 'Latin character symbol for the currency';
COMMENT ON COLUMN currency.display_name IS 'Currency name to display in text';
COMMENT ON COLUMN currency.full_name IS 'Full name of the fiat currency';
COMMENT ON COLUMN currency.html IS 'Character(s) for html display';
COMMENT ON COLUMN currency.format IS 'String containing default way to format. For example USD = "${:,.2f}"';
COMMENT ON COLUMN currency.token_type IS 'What type of token is this?';
COMMENT ON COLUMN currency.collateral_currency_backed_by IS 'Link to collateral that backs it';
COMMENT ON COLUMN currency.collateral_currency_pegged_to IS 'Link to price is it pegged to';

INSERT INTO currency (display_name, full_name, symbol, code, html, active_fiat) VALUES ('Dollar', 'United States Dollar', '$', 'USD', '&dollar;', true);
INSERT INTO currency (display_name, full_name, symbol, code, html, token_address, decimals, active_fiat) VALUES ('CSP', 'Casper', 'C', 'CSP', 'C', 'CSP', 9, false);
INSERT INTO currency (display_name, full_name, token_address, decimals) SELECT token_symbol, token_name, token_address, token_decimals FROM erc20_token;

-- Exchange Rate table
CREATE TABLE IF NOT EXISTS exchange_rate (
	id                   serial primary key,
	currency             integer                    NOT NULL,
	base_currency        integer                    NOT NULL,
	timestamp_utc        timestamp with time zone   NOT NULL,
	"open"               numeric(24,16),
	high                 numeric(24,16),
	low                  numeric(24,16),
	"close"              numeric(24,16),
	ath                  numeric(24,16),
	hrs_since_ath        bigint,
	CONSTRAINT one_price_per_hour UNIQUE ( currency, base_currency, timestamp_utc )
 );

CREATE INDEX IF NOT EXISTS base_currency ON exchange_rate  ( base_currency );
CREATE INDEX IF NOT EXISTS exchange_rate_close ON exchange_rate  ( "close" );
CREATE INDEX IF NOT EXISTS idx_timestamp ON exchange_rate  ( timestamp_utc );

-- Network table
CREATE TABLE IF NOT EXISTS network (
	id                          SERIAL PRIMARY KEY,
	"name"                      varchar(100)  NOT NULL,
	network_type                varchar(30)  NOT NULL,
	network_id                  integer,
	fl_db_name                  varchar(100),
    native_currency_table       varchar(25),
	abbr                        varchar(10),
	currency_id                 integer,
	token_url_prefix            varchar(255),
	lp_url_prefix               varchar(255),
	display_name                varchar(5),
	tx_api_network_identifier   varchar(20),
	CONSTRAINT unq_network_network_id UNIQUE ( network_id )
 );

ALTER TABLE network ADD CONSTRAINT fk_network_currency_id FOREIGN KEY ( currency_id ) REFERENCES currency( id );

COMMENT ON COLUMN network.network_type IS 'Text name of the network';
COMMENT ON COLUMN network.network_id IS 'The Network ID';
COMMENT ON COLUMN network.fl_db_name IS 'Name of the FLUIDEFI database that stores the network data';
COMMENT ON COLUMN network.abbr IS 'Abbreviation for network';
COMMENT ON COLUMN network.currency_id IS 'Primary currency used on this network (for pricing purposes)';
COMMENT ON COLUMN network.token_url_prefix IS 'URL for scan utility for tokens';
COMMENT ON COLUMN network.lp_url_prefix IS 'URL for scan utility for liquidity pools';

INSERT INTO network (name, network_type, network_id, fl_db_name, native_currency_table, abbr, display_name, tx_api_network_identifier) VALUES ('Casper Mainnet', 'Casper', 1101, 'postgres', 'native_price_usd', 'cspr', 'CSP', 'cspr_mainnet');
INSERT INTO network (name, network_type, network_id, fl_db_name, native_currency_table, abbr, display_name, tx_api_network_identifier) VALUES ('Casper Testnet', 'Casper', 1102, 'postgres', 'native_price_usd', 'cspr', 'CSP', 'cspr_testnet');
UPDATE currency SET network_id=subquery.id FROM (SELECT id FROM network WHERE network.name = 'Casper Testnet') AS subquery;
UPDATE network SET currency_id=subquery.id FROM (SELECT id FROM currency WHERE currency.display_name = 'WCSPR') AS subquery WHERE network.name = 'Casper Testnet';

-- Platform table
CREATE TABLE IF NOT EXISTS platform (
	id                   SERIAL PRIMARY KEY,
	"name"               varchar(100)   NOT NULL,
	full_name            varchar(100),
	router_address       varchar(42),
	factory_address      varchar(42),
	network              integer,
	symbol               varchar(5),
	url                  varchar(255),
	url_prefix           varchar(255),
	platform_type        integer        DEFAULT 5 NOT NULL,
	fl_supported         boolean        DEFAULT false,
	platform_image_path  varchar(255),
	token_url_prefix     varchar(255),
	lp_url_prefix        varchar(255),
    CONSTRAINT unq_platform_full_name UNIQUE ( full_name )
 );
INSERT INTO platform (name, full_name, network, fl_supported) VALUES ('Casperswap', 'Casperswap v1', 1, false);
INSERT INTO platform (name, full_name, network, fl_supported) VALUES ('Casperswap', 'Casperswap Beta', 2, true);
UPDATE platform SET network=subquery.id FROM (SELECT id FROM network WHERE network.name = 'Casper Mainnet') AS subquery WHERE platform.full_name = 'Casperswap v1';
UPDATE platform SET network=subquery.id FROM (SELECT id FROM network WHERE network.name = 'Casper Testnet') AS subquery WHERE platform.full_name = 'Casperswap Beta';

-- Summary Type table
CREATE TABLE IF NOT EXISTS summary_type (
    id                  SERIAL PRIMARY KEY,
    summary_description VARCHAR(100),
    data_frequency      VARCHAR(3),
    general_description VARCHAR(100)
);
CREATE UNIQUE INDEX IF NOT EXISTS unq_summary_type_df ON summary_type ( data_frequency );

-- Populate summary_type with lookup values
INSERT INTO summary_type (summary_description, data_frequency, general_description) VALUES ('Liquidity Pool Daily Summary', 'D', 'Day');
INSERT INTO summary_type (summary_description, data_frequency, general_description) VALUES ('Liquidity Pool Monthly Summary', 'M', 'Month');
INSERT INTO summary_type (summary_description, data_frequency, general_description) VALUES ('Liquidity Pool Trailing 24 Hour Summary', 't1d', NULL);
INSERT INTO summary_type (summary_description, data_frequency, general_description) VALUES ('Liquidity Pool Trailing 7 Day Summary', 't7d', NULL);
INSERT INTO summary_type (summary_description, data_frequency, general_description) VALUES ('Liquidity Pool Trailing 30 Day Summary', 't30', NULL);
INSERT INTO summary_type (summary_description, data_frequency, general_description) VALUES ('Liquidity Pool Trailing Quarterly Summary', 'tq', NULL);
INSERT INTO summary_type (summary_description, data_frequency, general_description) VALUES ('Liquidity Pool Trailing 12 Month Summary', 't12', NULL);


-- Pricing Tokens
CREATE TABLE IF NOT EXISTS pricing_tokens (
    id                  SERIAL PRIMARY KEY,
	token_address       varchar(100)                NOT NULL,
    network_id          integer                     NOT NULL,
	symbol              varchar(100)                NOT NULL,
	date_added          timestamp with time zone    DEFAULT CURRENT_TIMESTAMP,
	is_usd_stable_coin  boolean                     NOT NULL,
	constraint pricing_token_unique
        unique (token_address, network_id)
 );
INSERT INTO pricing_tokens (token_address, network_id, symbol, is_usd_stable_coin) VALUES ('0885c63f5f25ec5b6f3b57338fae5849aea5f1a2c96fc61411f2bfc5e432de5a', 2, 'WCSPR',  false);
INSERT INTO pricing_tokens (token_address, network_id, symbol, is_usd_stable_coin) VALUES ('e43357d2be4f5cd2d744e218eb7bf79148f0fa777b111a71c6d587f054a50b44', 2, 'USDC',  true);
-- No USDC paired LP INSERT INTO pricing_tokens (token_address, network_id, symbol, is_usd_stable_coin) VALUES ('31b15936ee5276803212bcde81a55ec2bd193fcd052256c111373fabe8facab0', 1102, 'DAI',  true);
INSERT INTO pricing_tokens (token_address, network_id, symbol, is_usd_stable_coin) VALUES ('a7672d33a577d196a42b9936025c2edc22b25c20cc16b783a3790c8e35f71e0b', 2, 'USDT',  true);

-- Casper Price
CREATE VIEW IF NOT EXISTS cspr_price AS SELECT * FROM native_price_usd;

-- Liquidity Pools
 CREATE TABLE IF NOT EXISTS liquidity_pool ( 
	id                          SERIAL PRIMARY KEY,
	"name"                      varchar(100),
	full_name                   varchar(100),
	fee_taken                   double precision,
	fee_earned                  double precision,
	url                         varchar(255),
	contract_address            varchar(100)                NOT NULL,
    network_id                  integer,
    platform_id                 integer,
	created_at_block_number     integer,
	created_at_timestamp_utc    timestamp with time zone,
	token0_symbol               varchar(12),
	token1_symbol               varchar(12),
	token0_address              varchar(100),
	token1_address              varchar(100),
	token0_collateral           integer,
	token1_collateral           integer,
	lp_token0_id                integer,
	lp_token1_id                integer,
	lp_watchlevel               integer    DEFAULT 1,
	notes                       text,
	last_processed              timestamp with time zone    DEFAULT CURRENT_TIMESTAMP,
	constraint liquidity_pool_unique
        unique (contract_address, network_id)
 );

CREATE INDEX idx_liquidity_pool ON liquidity_pool  ( name );
CREATE UNIQUE INDEX idx_liquidity_pool_contract_address ON liquidity_pool  ( contract_address, network_id );
INSERT INTO liquidity_pool (contract_address, created_at_block_number, created_at_timestamp_utc, token0_address, token1_address, fee_taken, fee_earned)
SELECT contract_address, first_mint_event_block_number, first_mint_event_timestamp_utc, token0_address, token1_address, 0.003, 0.0025
FROM all_pairs;
UPDATE liquidity_pool SET network_id=subquery.id FROM (SELECT id FROM network WHERE network.name = 'Casper Testnet') AS subquery;
UPDATE liquidity_pool SET platform_id=subquery.id FROM (SELECT id FROM platform WHERE platform.full_name = 'Casperswap Beta') AS subquery;

UPDATE liquidity_pool SET lp_token0_id=subquery.id, token0_symbol=subquery.display_name
FROM (SELECT token_address, id, display_name FROM currency) AS subquery WHERE liquidity_pool.token0_address=subquery.token_address;

UPDATE liquidity_pool SET lp_token1_id=subquery.id, token1_symbol=subquery.display_name
FROM (SELECT token_address, id, display_name FROM currency) AS subquery WHERE liquidity_pool.token1_address=subquery.token_address;
UPDATE liquidity_pool SET name=CONCAT(liquidity_pool.token0_symbol, '-', liquidity_pool.token1_symbol);
UPDATE liquidity_pool SET url='https://testnet.casperswap.xyz/pools';
UPDATE liquidity_pool SET last_processed=created_at_timestamp_utc;

CREATE TABLE IF NOT EXISTS lp_summary (
    id                      SERIAL PRIMARY KEY,
    liquidity_pool_id       integer,
	summary_type            integer,
	open_timestamp_utc      timestamp with time zone,
    close_timestamp_utc     timestamp with time zone,
	total_period_return     double precision,
	yield_on_lp_fees        double precision,
	price_change_ret        double precision,
	hodl_return             double precision,
    fees_apy                double precision,
    total_apy               double precision,
    impermanent_loss_level  double precision,
    impermanent_loss_impact double precision,
    volume                  double precision,
    transactions_period     integer,
    poolsize                double precision,
    open_poolsize           double precision,
	close_poolsize          double precision,
    open_reserve_0          double precision,
    open_reserve_1          double precision,
    close_reserve_0         double precision,
    close_reserve_1         double precision,
    open_price_0            double precision,
    open_price_1            double precision,
    high_price_0            double precision,
    high_price_1            double precision,
    low_price_0             double precision,
    low_price_1             double precision,
    close_price_0           double precision,
    close_price_1           double precision,
    constraint lp_summary_close
        unique (liquidity_pool_id, summary_type, close_timestamp_utc)
);

-- lp_recent view
CREATE VIEW lp_recent AS SELECT lps.id,
    lp.id AS liquidity_pool_id,
    lp.name AS lp_name,
    lp.fee_taken,
    lp.fee_earned,
    lps.summary_type,
    lps.open_timestamp_utc,
    lps.close_timestamp_utc,
    lp.created_at_timestamp_utc,
    lp.last_processed,
    lp.platform_id,
    platform.name AS platform_name,
    platform.network AS network_id,
    lp.contract_address,
    lp.url,
    lp.token0_symbol,
    lp.token1_symbol,
    lp.token0_address,
    lp.token1_address,
    lp.token0_collateral,
    lp.token1_collateral,
    lps.total_period_return,
    lps.total_apy,
    lps.yield_on_lp_fees,
    lps.fees_apy,
    lps.price_change_ret,
    lps.hodl_return,
    lps.impermanent_loss_level,
    lps.impermanent_loss_impact,
    lps.volume,
    lps.transactions_period,
    lps.open_reserve_0,
    lps.open_reserve_1,
    lps.close_reserve_0,
    lps.close_reserve_1,
    lps.poolsize,
    lps.open_poolsize,
    lps.close_poolsize,
    lps.open_price_0,
    lps.open_price_1,
    lps.high_price_0,
    lps.high_price_1,
    lps.low_price_0,
    lps.low_price_1,
    lps.close_price_0,
    lps.close_price_1,
    lp.lp_watchlevel,
    lp.notes
   FROM lp_summary lps
     JOIN liquidity_pool lp ON lps.liquidity_pool_id = lp.id
     JOIN platform ON lp.platform_id = platform.id
  ORDER BY lp.id, lps.summary_type, lps.close_timestamp_utc DESC;

-- 
CREATE TABLE IF NOT EXISTS user_filters (
	id                      SERIAL PRIMARY KEY,
	user_id                 integer,
	use_filters             boolean DEFAULT true,
	filter_version          integer,
	collateral_fiat         boolean DEFAULT true NOT NULL,
	collateral_crypto       boolean DEFAULT true NOT NULL,
	collateral_algorithmic  boolean DEFAULT true NOT NULL,
	collateral_metals       boolean DEFAULT true NOT NULL,
	collateral_other        boolean DEFAULT true NOT NULL,
	poolsize_min            integer DEFAULT 50000 NOT NULL,
	poolsize_max            bigint,
	volume_min              integer DEFAULT 5000 NOT NULL,
	volume_max              bigint,
	ill_min                 double precision,
	ill_max                 double precision,
	yff_min                 double precision,
	transactions_min_day    integer DEFAULT 0 NOT NULL,
	transactions_min_week   integer DEFAULT 10 NOT NULL,
	pool_size_t1d_min       integer,
	pool_size_t1d_max       integer,
	pool_size_t7d_min       integer,
	pool_size_t7d_max       integer,
	volume_t1d_min          integer,
	volume_t1d_max          integer,
	volume_t7d_min          integer,
	volume_t7d_max          integer
 );
-- IMPORTANT NOTE: The fk that references auth_user cannot be created until Django database migration is performed
ALTER TABLE user_filters ADD CONSTRAINT fk_user_filters_auth_user FOREIGN KEY ( user_id ) REFERENCES auth_user( id );

-- model_type
CREATE TABLE IF NOT EXISTS model_type (
	id                   SERIAL PRIMARY KEY,
	model_name           varchar(50)
 );

-- User Liquidity Pool list
CREATE TABLE IF NOT EXISTS user_lp_list (
	id                              SERIAL PRIMARY KEY,
	user_id                         integer,
	lp_list_name                    varchar(100),
	timestamp_utc                   timestamptz DEFAULT CURRENT_TIMESTAMP,
	model_type_id                   integer,
	investment_size                 double precision,
	investment_timestamp_utc        timestamptz,
	investment_end_timestamp_utc    timestamptz DEFAULT CURRENT_TIMESTAMP,
	currency_id                     integer
 );
-- IMPORTANT NOTE: The fk that references auth_user cannot be created until Django database migration is performed 
ALTER TABLE user_lp_list ADD CONSTRAINT fk_user_lp_list_auth_user FOREIGN KEY ( user_id ) REFERENCES auth_user( id );
ALTER TABLE user_lp_list ADD CONSTRAINT fk_user_lp_list_model_type FOREIGN KEY ( model_type_id ) REFERENCES model_type( id );
ALTER TABLE user_lp_list ADD CONSTRAINT fk_user_lp_list_currency FOREIGN KEY ( currency_id ) REFERENCES currency( id );

-- Liquidity Pool List
CREATE TABLE IF NOT EXISTS lp_list (
	id                   SERIAL PRIMARY KEY,
	lp_list_id           integer,
	liquidity_pool_id    integer,
	contract_address     varchar(42),
	lp_amount            numeric(64,0),
	currency_id          integer,
	token_address        varchar(100),
	token_amount         numeric(64,0) DEFAULT 0,
	weight               double precision,
	lp_balance_eth       numeric(64,0) DEFAULT 0,
	lp_list_percentage   double precision,
	lp_token_amount      numeric(64,0) DEFAULT 0
 );
CREATE INDEX idx_lp_list ON lp_list  ( lp_list_id, liquidity_pool_id );
CREATE INDEX idx_lp_list_token_address ON lp_list  ( token_address );
CREATE INDEX idx_lp_list_token ON lp_list  ( lp_list_id, currency_id );
ALTER TABLE lp_list ADD CONSTRAINT fk_lp_list_user_lp_list FOREIGN KEY ( lp_list_id ) REFERENCES user_lp_list( id ) ON DELETE CASCADE;
ALTER TABLE lp_list ADD CONSTRAINT fk_lp_list_liquidity_pool FOREIGN KEY ( liquidity_pool_id ) REFERENCES liquidity_pool( id );
ALTER TABLE lp_list ADD CONSTRAINT fk_lp_list_currency_id FOREIGN KEY ( currency_id ) REFERENCES currency( id );

-- lp_summary_3
-- CREATE TABLE lp_summary_3 (
--	id                      SERIAL PRIMARY KEY,
--	liquidity_pool_id       integer  NOT NULL,
--	timestamp_utc           timestamp with time zone,
--	open_lp_token_supply    double precision,
--	close_lp_token_supply   double precision,
--	num_swaps_0             integer,
--	num_swaps_1             integer,
--	num_burns               integer,
--	num_mints               integer,
--	volume_0                double precision,
--	volume_1                double precision,
--	open_reserve_0          double precision,
--	close_reserve_0         double precision  NOT NULL,
--	open_reserve_1          double precision,
--	close_reserve_1         double precision  NOT NULL
-- );
-- CREATE INDEX idx_lp_summary_3_lp_id ON lp_summary_3  ( liquidity_pool_id );
-- CREATE INDEX idx_lp_summary_3_lp_id_timestamp ON lp_summary_3  ( liquidity_pool_id, timestamp_utc );

-- liquidity pool last processed dates
-- CREATE VIEW lp_3_processing_dates AS
--  SELECT liquidity_pool.contract_address,
--     COALESCE (max(lp_summary_3.timestamp_utc), max(liquidity_pool.last_processed)) AS latest_lp_summary_3_record_date,
--     max(liquidity_pool.last_processed) AS last_processed,
--     max(liquidity_pool.id) AS liquidity_pool_id
--    FROM lp_summary_3
--      RIGHT JOIN liquidity_pool ON lp_summary_3.liquidity_pool_id = liquidity_pool.id
--   WHERE liquidity_pool.lp_watchlevel = 1
--   GROUP BY liquidity_pool.contract_address;

-- Materialize View (will be refreshed every hour)
CREATE MATERIALIZED VIEW IF NOT EXISTS fungible_token_pricing AS
 WITH er_latest AS (
         SELECT DISTINCT ON (exchange_rate.base_currency) exchange_rate.base_currency,
            exchange_rate.timestamp_utc AS latest_price_timestamp,
            exchange_rate.ath AS latest_ath,
            exchange_rate.hrs_since_ath AS latest_hrs_since_ath
           FROM exchange_rate
          ORDER BY exchange_rate.base_currency, exchange_rate.timestamp_utc DESC
        ), pricing_pools AS (
         SELECT liquidity_pool.name,
            liquidity_pool.platform_id,
            liquidity_pool.contract_address,
            liquidity_pool.token0_address AS pricing_token_address,
            liquidity_pool.lp_watchlevel,
            pricing_tokens.is_usd_stable_coin,
            liquidity_pool.token1_address AS target_token_address,
                CASE
                    WHEN pricing_tokens.id IS NULL THEN false
                    ELSE true
                END AS is_pricing_token,
            1 AS target_token_idx
           FROM liquidity_pool liquidity_pool
             FULL JOIN pricing_tokens ON pricing_tokens.token_address::text = liquidity_pool.token0_address::text
        UNION ALL
         SELECT liquidity_pool.name,
            liquidity_pool.platform_id,
            liquidity_pool.contract_address,
            liquidity_pool.token1_address AS pricing_token_address,
            liquidity_pool.lp_watchlevel,
            pricing_tokens.is_usd_stable_coin,
            liquidity_pool.token0_address AS target_token_address,
                CASE
                    WHEN pricing_tokens.id IS NULL THEN false
                    ELSE true
                END AS is_pricing_token,
            0 AS target_token_idx
           FROM liquidity_pool liquidity_pool
             FULL JOIN pricing_tokens ON pricing_tokens.token_address::text = liquidity_pool.token1_address::text
        )
 SELECT DISTINCT pricing_pools.target_token_address,
    currency.id AS target_token_id,
    er_latest.latest_price_timestamp,
    er_latest.latest_ath,
    er_latest.latest_hrs_since_ath,
    liquidity_pool.created_at_timestamp_utc AS pool_creation_timestamp_utc,
    liquidity_pool.created_at_block_number,
    pricing_pools.name AS pool_name,
    platform.platform_type,
    platform.network,
    pricing_pools.contract_address AS pool_address,
    pricing_pools.pricing_token_address,
    pricing_pools.target_token_idx,
    pricing_pools.lp_watchlevel,
    pricing_pools.is_usd_stable_coin,
    pricing_pools.is_pricing_token,
    lp_recent.close_poolsize AS latest_poolsize,
    network.fl_db_name,
    network.abbr AS network_token_symbol,
    network.native_currency_table,
        CASE
            WHEN network.currency_id = currency.id THEN true
            ELSE false
        END AS is_network_currency,
    timezone('utc'::text, now()) AS refresh_timestamp_utc
   FROM pricing_pools
     LEFT JOIN lp_recent ON pricing_pools.contract_address::text = lp_recent.contract_address::text
     LEFT JOIN liquidity_pool ON pricing_pools.contract_address::text = liquidity_pool.contract_address::text
     LEFT JOIN platform ON platform.id = pricing_pools.platform_id
     LEFT JOIN network ON platform.network = network.id
     LEFT JOIN currency ON currency.token_address::text = pricing_pools.target_token_address::text AND currency.network_id = platform.network
     LEFT JOIN er_latest ON er_latest.base_currency = currency.id
  WHERE platform.fl_supported = true AND ((lp_recent.id IN ( SELECT DISTINCT ON (lp_recent.contract_address) lp_recent.id
           FROM lp_recent lp_recent
          ORDER BY lp_recent.contract_address, lp_recent.close_timestamp_utc DESC)) OR lp_recent.id IS NULL);

CREATE UNIQUE INDEX idx_fungible_token_pricing_pk ON fungible_token_pricing (pool_address NULLS FIRST, network, target_token_address);

-- Refresh the materialized view after data is loaded
REFRESH MATERIALIZED VIEW CONCURRENTLY fungible_token_pricing;

-- DB security and access control
GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO postgres;

CREATE ROLE owner_m_views WITH NOLOGIN;
GRANT USAGE ON SCHEMA public TO owner_m_views;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO owner_m_views;
GRANT ALL PRIVILEGES ON fungible_token_pricing TO owner_m_views;
ALTER MATERIALIZED VIEW fungible_token_pricing OWNER TO owner_m_views;
GRANT owner_m_views TO postgres WITH ADMIN OPTION;

ALTER TABLE all_pairs            OWNER TO postgres;
ALTER TABLE block_hours          OWNER TO postgres;
ALTER TABLE block_summary        OWNER TO postgres;
ALTER TABLE blocks               OWNER TO postgres;
ALTER TABLE currency             OWNER TO postgres;
ALTER TABLE deploys              OWNER TO postgres;
ALTER TABLE django_migrations    OWNER TO postgres;
ALTER TABLE erc20_approval_event OWNER TO postgres;
ALTER TABLE erc20_token          OWNER TO postgres;
ALTER TABLE erc20_transfer_event OWNER TO postgres;
ALTER TABLE exchange_rate        OWNER TO postgres;
ALTER TABLE hourly_data          OWNER TO postgres;
ALTER TABLE liquidity_pool       OWNER TO postgres;
ALTER TABLE lp_summary           OWNER TO postgres;
ALTER TABLE lp_summary_3         OWNER TO postgres;
ALTER TABLE native_price_usd     OWNER TO postgres;
ALTER TABLE network              OWNER TO postgres;
ALTER TABLE pair_created_event   OWNER TO postgres;
ALTER TABLE platform             OWNER TO postgres;
ALTER TABLE prefix               OWNER TO postgres;
ALTER TABLE pricing_tokens       OWNER TO postgres;
ALTER TABLE process_log          OWNER TO postgres;
ALTER TABLE raw_pair_burn_event  OWNER TO postgres;
ALTER TABLE raw_pair_mint_event  OWNER TO postgres;
ALTER TABLE raw_pair_swap_event  OWNER TO postgres;
ALTER TABLE raw_pair_sync_event  OWNER TO postgres;
ALTER TABLE summary_type         OWNER TO postgres;
ALTER TABLE token_total_supply   OWNER TO postgres;
ALTER TABLE model_type           OWNER TO postgres;
ALTER TABLE user_lp_list         OWNER TO postgres;
ALTER TABLE lp_list              OWNER TO postgres;
ALTER TABLE user_filters         OWNER TO postgres;


-- The below may need to be performed after the Django migrations
-- execute as the postgres user that run the Django migration
ALTER TABLE auth_group                                OWNER TO postgres;
ALTER TABLE auth_group_id_seq                         OWNER TO postgres;
ALTER TABLE auth_group_permissions                    OWNER TO postgres;
ALTER TABLE auth_group_permissions_id_seq             OWNER TO postgres;
ALTER TABLE auth_permission                           OWNER TO postgres;
ALTER TABLE auth_permission_id_seq                    OWNER TO postgres;
ALTER TABLE auth_user                                 OWNER TO postgres;
ALTER TABLE auth_user_groups                          OWNER TO postgres;
ALTER TABLE auth_user_groups_id_seq                   OWNER TO postgres;
ALTER TABLE auth_user_id_seq                          OWNER TO postgres;
ALTER TABLE auth_user_user_permissions                OWNER TO postgres;
ALTER TABLE auth_user_user_permissions_id_seq         OWNER TO postgres;
ALTER TABLE authtoken_token                           OWNER TO postgres;
ALTER TABLE django_admin_log                          OWNER TO postgres;
ALTER TABLE django_admin_log_id_seq                   OWNER TO postgres;
ALTER TABLE django_content_type                       OWNER TO postgres;
ALTER TABLE django_content_type_id_seq                OWNER TO postgres;
ALTER TABLE django_session                            OWNER TO postgres;
ALTER TABLE user_filters ADD CONSTRAINT fk_user_filters_auth_user FOREIGN KEY ( user_id ) REFERENCES auth_user( id );
ALTER TABLE user_lp_list ADD CONSTRAINT fk_user_lp_list_auth_user FOREIGN KEY ( user_id ) REFERENCES auth_user( id );

-- Default filters should be added after the first admin user is created
INSERT INTO user_filters ("id","user_id","collateral_fiat","collateral_crypto","collateral_algorithmic","collateral_metals","collateral_other","poolsize_min","volume_min","transactions_min_day","transactions_min_week","pool_size_t1d_min","pool_size_t1d_max","pool_size_t7d_min","pool_size_t7d_max","volume_t1d_min","volume_t1d_max","volume_t7d_min","volume_t7d_max","volume_max","poolsize_max","ill_min","ill_max","yff_min","filter_version","use_filters") VALUES (1,1,True,True,True,True,True,10000,1000,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,999999999,999999999,-9999.0,9999.99,-9999.0,1,True);