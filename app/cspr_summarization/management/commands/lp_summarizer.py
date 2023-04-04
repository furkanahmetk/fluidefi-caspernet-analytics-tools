# Usage example:
# python3 manage.py lp_summarizer cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0 --all --t30

import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

import datetime

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from datetime import datetime, timedelta, timezone

import traceback

# Models
from cspr_summarization.entities.SummaryType import SummaryType
from cspr_summarization.entities.LiquidityPool import LiquidityPool
from cspr_summarization.entities.LpSummary import LpSummary
from cspr_summarization.entities.HourlyData import HourlyData

from data_servers.db_connection_manager import DBConnectionManager
from data_servers.data_server import DataServer


class Command(BaseCommand):
    help = 'Summarizes Liquidity Pools v3'
    wait_for_summaries_loop_timeout = 10    # seconds

    def add_arguments(self, parser):
        parser.add_argument('contract_address', nargs='+', type=str)

        # Optional arguments (default is to process daily)
        parser.add_argument('--debug', action='store_true', help='Display additional information & limit to 20 LPs', )
        parser.add_argument('--all', action='store_true', help='Process all known LPs (Are you sure?)', )
        parser.add_argument('--overwrite', action='store_true', help='Overwrite existing data in table', )
        parser.add_argument('--t1d', action='store_true', help='Process trailing 24 hours up to the last hour (default)', )
        parser.add_argument('--daily', action='store_true', help='Process daily summary', )
        parser.add_argument('--d', action='store_true', help='Process daily summary', )
        parser.add_argument('--t7d', action='store_true', help='Process trailing 7 days up to the last hour', )
        parser.add_argument('--weekly', action='store_true', help='Process weekly summary', )
        parser.add_argument('--w', action='store_true', help='Process weekly summary', )
        parser.add_argument('--t30', action='store_true', help='Process trailing 30 days up to midnight', )
        parser.add_argument('--monthly', action='store_true', help='Process monthly summary', )
        parser.add_argument('--m', action='store_true', help='Process monthly summary', )
        parser.add_argument('--tq', action='store_true', help='Process trailing quarterly summary', )
        parser.add_argument('--t12', action='store_true', help='Process trailing 12 month summary', )

        parser.add_argument('--refresh', action='store_true', help='Refresh materialized view', )

    def handle(self, *args, **kwargs):
        debug = False
        allpairs = False
        overwrite = False
        refresh = False

        # date_format = '%Y-%m-%d %H:%M:%S'
        starttime = datetime.now(timezone.utc)
        self.stdout.write(self.style.HTTP_INFO("Summarizer starting at %s UTC " % starttime.strftime("%b-%d-%Y %H:%M")))
        if kwargs['debug']:
            debug = True

        if kwargs['all']:
            allpairs = True

        if kwargs['overwrite']:
            overwrite = True

        if kwargs['refresh']:
            refresh = True

        ###############################################################################################################
        # Refresh materialized views only when the --refresh flag is included in the command line
        if refresh:
            refresh_views()

        ###############################################################################################################
        # Get lookup table values
        if debug:
            print("Looking up data sources.")

        try:
            # Get a list of lp_ids
            pair_list = []
            if allpairs:
                pair_list = LiquidityPool.objects.using('default').filter(contract_address__isnull=False).order_by(
                    'last_processed', 'id').values_list('id', flat=True)

        except Exception as e:
            self.stdout.write("Could not retrieve liquidity pool data from DB. Exiting.")
            self.stdout.write(self.style.HTTP_INFO(e))
            exit(-1)

        lp_count = len(pair_list)
        print("Num of LPs found: ", lp_count)
        pair_process_cnt = 0
        counter = 1

        ###############################################################
        # Invoke Data Server
        db = DBConnectionManager()
        prod_us1_conn = db.get_connection("postgres", "r")
        fl_agg_conn = {1: db.get_connection("postgres", "r"),
                       2: db.get_connection("postgres", "rw")}

        data_server = DataServer(prod_us1_conn, fl_agg_conn)
        data_server.set_data_frequency("H")
        currency_id = 1                                         # Default to USD
        data_server.set_denomination_currency(currency_id)

        ###############################################################
        # Loop through liquidity pools
        for lp_id in pair_list:
            skip = False
            try:
                print(f"Processing liquidity pool ID: {lp_id} - {counter} of {lp_count} LPs. ")

                # Get the liquidity_pool
                lp_object = LiquidityPool.objects.using('default').get(id=lp_id)

                # Example = "2023-03-26 12:00:00+00"

                # Get the datetime the lp_summary_populator last completed for this liquidity pool
                last_processed = HourlyData.objects.using('default').filter(address=lp_object.contract_address).order_by('-close_timestamp_utc')[1]

                if last_processed is not None:
                    if debug:
                        print("FLUIDEFI processed up to timestamp UTC:", last_processed.close_timestamp_utc)
                else:
                    print("WARNING: Can not find any hourly data for this liquidity pool. Skipping...")
                    skip = True

                ###############################################################
                # Get the date range based on the last processed date
                if not skip:

                    # last_processed.max_block
                    if kwargs['daily'] or kwargs['d']:
                        # End at the top of the current hour
                        summary_type = SummaryType.objects.using('default').get(data_frequency="D")
                        # process_end_datetime = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0, hour=0)
                        process_end_datetime = last_processed.close_timestamp_utc.replace(microsecond=0, second=0, minute=0, hour=0)
                        end_datetime = process_end_datetime
                        start_datetime = (end_datetime - timedelta(days=1))

                    elif kwargs['weekly'] or kwargs['w']:
                        # End at midnight of the current day
                        summary_type = SummaryType.objects.using('default').get(data_frequency="W")
                        # process_end_datetime = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0, hour=0)
                        process_end_datetime = last_processed.close_timestamp_utc.replace(microsecond=0, second=0, minute=0, hour=0)
                        end_datetime = process_end_datetime  # lp_object.last_processed3
                        start_datetime = (end_datetime - timedelta(days=7))

                    elif kwargs['t7d']:
                        # End at the top of the hour
                        summary_type = SummaryType.objects.using('default').get(data_frequency="t7d")
                        # process_end_datetime = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0)
                        process_end_datetime = last_processed.close_timestamp_utc.replace(microsecond=0, second=0, minute=0)
                        end_datetime = process_end_datetime
                        start_datetime = (end_datetime - timedelta(days=7))

                    elif kwargs['monthly'] or kwargs['m']:
                        # Get the first day of this month and subtract 1 day
                        summary_type = SummaryType.objects.using('default').get(data_frequency="M")
                        # process_end_datetime = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0, hour=0, day=1)
                        process_end_datetime = last_processed.close_timestamp_utc.replace(microsecond=0, second=0, minute=0, hour=0,
                                                                                         day=1)
                        process_end_datetime = process_end_datetime - timedelta(days=1)
                        end_datetime = process_end_datetime
                        start_datetime = process_end_datetime.replace(microsecond=0, second=0, minute=0, hour=0, day=1)

                    elif kwargs['t30']:
                        # End at midnight of the current day
                        summary_type = SummaryType.objects.using('default').get(data_frequency="t30")
                        # process_end_datetime = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0, hour=0)
                        process_end_datetime = last_processed.close_timestamp_utc.replace(microsecond=0, second=0, minute=0)
                        end_datetime = process_end_datetime
                        start_datetime = (end_datetime - timedelta(days=30))

                    else:
                        # Default is t1d, the last 24 hours
                        summary_type = SummaryType.objects.using('default').get(data_frequency="t1d")
                        # process_end_datetime = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0)
                        process_end_datetime = last_processed.close_timestamp_utc.replace(microsecond=0, second=0, minute=0)
                        end_datetime = process_end_datetime
                        start_datetime = (end_datetime - timedelta(days=1))

                    data_server.set_date_range(start_datetime, end_datetime)

                    ###############################################################
                    # If overwrite is enabled, proceed; Otherwise, see if the record already exists
                    if overwrite:
                        print("Overwrite enabled; PROCESSING", summary_type.data_frequency)
                    else:                                   # Check if the summary is already there
                        try:
                            LpSummary.objects.using('default').get(liquidity_pool=lp_id,
                                                                    summary_type=summary_type,
                                                                    open_timestamp_utc=start_datetime,
                                                                    close_timestamp_utc=end_datetime)
                            print(f"{summary_type.data_frequency} summary record already exists; SKIPPING OVER {lp_object.name}")
                            skip = True
                        except LpSummary.DoesNotExist:
                            print(f"No {summary_type.data_frequency} summary record found; PROCESSING {lp_object.name}")
                        except Exception as e:
                            print("EXCEPTION: Error selecting existing summary record:", e)
                            pass

                    ###############################################################################################
                    # Call data_server with lp_summary_server
                    ###############################################################################################
                    if not skip:
                        try:
                            summary = data_server.lp_summary.get_lp_summary(lp_address=lp_object.contract_address,
                                                                            network=lp_object.network_id)
                            if debug:
                                print("lp_summary: ")
                                print(summary)

                        except Exception as e:
                            print("EXCEPTION: lp_summarizer calling get_lp_summary server:", e)
                            if debug:
                                print(traceback.format_exc())
                                if summary is not None:
                                    print(
                                        f"{lp_object.name} on network: {lp_object.network_id} Contract address: {lp_object.contract_address}")
                                    print(
                                        f"data_frequency: H | currency: {currency_id} | {start_datetime} to {end_datetime}")
                                    print(repr(e)[0:30])
                                    lp_object.last_processed = datetime.now(timezone.utc)
                                    lp_object.save(update_fields=['last_processed'])
                                    # "Couldn't find price for token"

                            skip = True

                    ###############################################################################################
                    # Skip required in case of exception. summary will be null
                    if not skip and debug:
                        print(f"Summary: {summary}")

                    # Check if data frame came back empty
                    if not skip and not summary:
                        print(f"WARNING: No data for period. {lp_object.name} - address: {lp_object.contract_address} on network: {lp_network} | data_frequency: H | currency: {currency_id} | {start_datetime} to {end_datetime}")
                        skip = True
                        lp_object.last_processed = datetime.now(timezone.utc)
                        lp_object.save(update_fields=['last_processed'])

            except Exception as e:
                print(e)
                pass

            try:
                if not skip:
                    lpsummary, createdSummary = LpSummary.objects.using('default').update_or_create(
                        liquidity_pool=lp_object,
                        summary_type=summary_type,
                        defaults={'open_timestamp_utc': start_datetime,
                                  'close_timestamp_utc': end_datetime,
                                  'total_period_return': summary["total_period_return"],
                                  'total_apy': summary["total_apy"],
                                  'yield_on_lp_fees': summary["yield_on_lp_fees"],
                                  'fees_apy': summary["fees_apy"],
                                  'price_change_ret': summary["price_change_ret"],
                                  'hodl_return': summary["hodl_return"],
                                  'impermanent_loss_level': summary["impermanent_loss_level"],
                                  'impermanent_loss_impact': summary["impermanent_loss_impact"],
                                  'volume': summary["volume"],
                                  'transactions_period': summary["transactions_period"],
                                  'poolsize': summary["close_poolsize"],
                                  'open_poolsize': summary["open_poolsize"],
                                  'close_poolsize': summary["close_poolsize"],
                                  'open_reserve_0': summary["open_reserve_0"],
                                  'open_reserve_1': summary["open_reserve_1"],
                                  'close_reserve_0': summary["close_reserve_0"],
                                  'close_reserve_1': summary["close_reserve_1"],
                                  'open_price_0': summary["open_price_0"],
                                  'open_price_1': summary["open_price_1"],
                                  'high_price_0': summary["high_price_0"],
                                  'high_price_1': summary["high_price_1"],
                                  'low_price_0': summary["low_price_0"],
                                  'low_price_1': summary["low_price_1"],
                                  'close_price_0': summary["close_price_0"],
                                  'close_price_1': summary["close_price_1"]
                                  })
                    if debug:
                        print(f"{lp_object.name} {lp_object.fee_taken} UPDATED {summary_type.data_frequency} for {start_datetime} to {end_datetime}")

                    lp_object.last_processed = datetime.now(timezone.utc)
                    lp_object.save(update_fields=['last_processed'])
                    pair_process_cnt += 1

            except Exception as e:
                print(traceback.format_exc())
                print(e)
                self.stdout.write("EXCEPTION: Cannot save LpSummary record.")
                self.stdout.write(self.style.HTTP_INFO(e))

            ###########################################################################################
            # Clean up old summaries for this liquidity pool that don't match the current period
            ###########################################################################################
            try:
                old_summaries = LpSummary.objects.using('default').filter(liquidity_pool_id=lp_id,
                                                                            summary_type=summary_type).exclude(
                                                                            open_timestamp_utc=start_datetime,
                                                                            close_timestamp_utc=end_datetime)
                if not skip and old_summaries.exists():
                    # print(old_summaries)
                    print(f"Deleting {old_summaries.count()} old summary {summary_type.data_frequency} records exist for {lp_id}")
                    old_summaries.delete()
                else:
                    if debug:
                        print(f"No old summary {summary_type.data_frequency} records exist for {lp_id}")
            except LpSummary.DoesNotExist:
                print(f"No old summary {summary_type.data_frequency} records exist for {lp_id}")
            except Exception as e:
                print("Exception error for existing summary record:", e)
                pass

            ###########################################################################################
            # Next LP
            ###########################################################################################
            counter += 1
            print("###########################################################################################")

        print("###########################################################################################")
        self.stdout.write(self.style.HTTP_INFO("Summarizer stored %s liquidity pools" % pair_process_cnt))


@transaction.atomic
def refresh_views():
    starttime = datetime.now(timezone.utc)
    print("=========================")
    print("REFRESH MATERIALIZED VIEW started at %s UTC " % starttime.strftime("%b-%d-%Y %H:%M"))

    try:
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY fungible_token_pricing")  # Remove CONCURRENTLY if table empty
    except Exception as e:
        print("*************************")
        print("EXCEPTION: CANNOT REFRESH MATERIALIZED VIEW.")
        print("*************************")
        print(e)
        pass

    endtime = datetime.now(timezone.utc)
    print("REFRESH MATERIALIZED VIEW at %s UTC" % endtime.strftime("%b-%d-%Y %H:%M"))
    difftime = endtime - starttime
    print("REFRESH took %s" % difftime)
    print("=========================")