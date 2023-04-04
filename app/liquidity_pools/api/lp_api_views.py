from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import traceback
from pathlib import Path
import os
import sys
import numpy as np

from django.db.models import  F

cwd = os.getcwd()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(BASE_DIR)
sys.path.append(str(BASE_DIR))

from filters.api.filters import get_filters

from cspr_summarization.entities.LpList import LpList
from cspr_summarization.entities.LpRecent import LpRecent
from cspr_summarization.entities.SummaryType import SummaryType
from cspr_summarization.entities.UserFilters import UserFilters
from cspr_summarization.entities.UserLpList import UserLpList
from cspr_summarizers.serializers import lpV3Serializer


###############################################################
# GET LIQUIDITY POOLS BY
# Get the number of Liquidity Pools sorted by parameter
# param 1: sorting option (always descending, highest to lowest)
# valid options are: apr, fees, size, trans, vol, new
# param 2: number of pools, up to 100
# param 3: time period in days: 1 = 1 Day, 7 = 1 week
# example: /lp/apr/20/7/
# https://praggus01.fluidefi.io/lp/apr/10/7/  <= top 10 pools by apr (period performance) for the week (same as top_rank)
# https://praggus01.fluidefi.io/lp/fees/10/7/  <= top 10 pools by fees for the week
# https://praggus01.fluidefi.io/lp/size/20/1/  <= top 20 pools by pool size for the day
# https://praggus01.fluidefi.io/lp/trans/5/1/ <= top 5 pools by transactions for the day
# https://praggus01.fluidefi.io/lp/vol/5/7/ <= top 5 pools by volume for the week
# https://praggus01.fluidefi.io/lp/new/10/1/  <= newest 10 liquidity pools with data for the day
# https://praggus01.fluidefi.io/lp/favorites/10/1/ <= Favorites (first 10 sorted alphabetically) with 1 day worth of data
# https://praggus01.fluidefi.io/lp/portfolio/3/1/ <= Portfolio # 3 (sorted alphabetically) with 1 day worth of data
###############################################################
# Used for production API; Desktop APP uses legacy version get_lp_by() in api_published.py

class lp_by(APIView):
    @extend_schema(
        summary="GET Liquidity Pools by...",
        description="Get details for the top performing liquidity pools, sorted as specified, for the time period specified. Returns up to 100 results.",
        parameters=[
            OpenApiParameter(
                name='Authorization',
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description='{{UserToken}} <br>'
                            '"Token " + token returned during authentication.'
            ),
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
                description="sort_option: " + \
                            "<table>" + \
                            "<tr><td>apy</td><td>Total rate of return of a liquidity pool in the specified period, sorted in descending order, greatest to lowest</td></tr>" + \
                            "<tr><td>pcr</td><td>Return from the change in price of a liquidity pool's underlying tokens in the specified period, sorted in descending order, greatest to lowest</td></tr>" + \
                            "<tr><td>fees</td><td>Return from fees of a liquidity pool in the specified period, sorted in descending order, greatest to lowest</td></tr>" + \
                            "<tr><td>ill</td><td>Impermanent loss level, sorted in ascending order, lowest to greatest</td></tr>" + \
                            "<tr><td>hodl</td><td>Total return of a hodl'er in the specified period, sorted in descending order, greatest to lowest</td></tr>" + \
                            "<tr><td>size</td><td>Size of liquidity pool in USD, sorted in descending order, greatest to lowest</td></tr>" + \
                            "<tr><td>trans</td><td>Number of transactions in the specified period, sorted in descending order, highest to least</td></tr>" + \
                            "<tr><td>events</td><td>Number of adds, and removes in the specified period, sorted in descending order, highest to least</td></tr>" + \
                            "<tr><td>vol</td><td>Volume in USD in the specified period, sorted in descending order, greatest to lowest</td></tr>" + \
                            "<tr><td>new</td><td>New liquidity pools, sorted by most recently created to oldest</td></tr>" + \
                            "<tr><td>favorites</td><td>Liquidity pools marked as favorites, sorted in alphabetical order</td></tr>" + \
                            "<tr><td>portfolio</td><td>Liquidity pools in the portfolio specified in the lp_pool_num parameter, sorted in alphabetical order</td></tr>" + \
                            "</table>"
            ),
            OpenApiParameter(
                name='sk',
                type=int,
                location=OpenApiParameter.PATH,
                required=True,
                description="lp_pool_num: For all sort_options except watchlist & portfolio, number of pools to " + \
                            "include in results, up to 100."
            ),
            OpenApiParameter(
                name='tk',
                type=int,
                location=OpenApiParameter.PATH,
                required=True,
                description="time_period: Time period in days:<br/> " + \
                            "<table>" + \
                            "<tr><td>1</td><td>1 Day (trailing 24 hours)</td></tr>" + \
                            "<tr><td>7</td><td>1 week (trailing 7 days)</td></tr>" + \
                            "<tr><td>30</td><td>1 month (trailing 30 days)</td></tr>" + \
                            "<tr><td>31</td><td>Previous month</td></tr>" + \
                            "<tr><td>90</td><td>90 Days (trailing quarterly summary)</td></tr>" + \
                            "<tr><td>365</td><td>365 Days (trailing 12 month summary)</td></tr>" + \
                            "</table>" + \
                            "Check subscription level for accessibility."
            ),
        ],
        tags=["Liquidity Pool Analytics"],
        extensions={
            'x-code-samples': [
                {'lang': 'bash', 'label': 'Example', 'source': '''
                 curl --location --request GET '{{host}}/lp/{{sort_option}}/{{lp_pool_num}}/{{time_period}}/' '''
                 },
            ],
        },
        examples=[OpenApiExample(
            name="Response",
            response_only=True,
            value=[
                {
                    "id": 24705095,
                    "liquidity_pool_id": 172172,
                    "lp_name": "TAIL-WETH",
                    "open_timestamp_utc": "2023-03-31T13:00:00",
                    "close_timestamp_utc": "2023-04-01T13:00:00",
                    "platform_id": "213",
                    "platform_name": "Uniswap V3",
                    "fee_taken": 0.01,
                    "fee_earned": 0.01,
                    "contract_address": "0xbED8674cF009214A1209e61133215e5F81487fD9",
                    "url": "https://info.uniswap.org/#/pools/0xbed8674cf009214a1209e61133215e5f81487fd9",
                    "created_at_timestamp_utc": "2023-03-10T13:52:59",
                    "token0_symbol": "TAIL",
                    "token1_symbol": "WETH",
                    "token0_address": "0x4384b85FE228AE727B129230211194E4A50877c4",
                    "token1_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "token0_collateral": "6",
                    "token1_collateral": "5",
                    "total_period_return": 23.649,
                    "total_apy": 8631.994,
                    "yield_on_lp_fees": 1.016,
                    "fees_apy": 370.885,
                    "price_change_ret": 22.633,
                    "misc_return": 0.0,
                    "hodl_return": 11.002,
                    "open_lp_token_price": 0.0,
                    "close_lp_token_price": 0.0,
                    "token_0_price_return": 20.85,
                    "token_1_price_return": 1.154,
                    "impermanent_loss_level": -0.3191,
                    "impermanent_loss_impact": -0.3542,
                    "volume_0": 11850389472620.95,
                    "volume_1": 9.599,
                    "volume_0_base_curr": 17686.488,
                    "volume_1_base_curr": 17542.599,
                    "volume": 35229.088,
                    "avg_daily_vol": 37519.308,
                    "transactions_period": 71.0,
                    "num_swaps": 69,
                    "avg_swap_size": 543.758,
                    "active_positions": 2,
                    "active_wallets": 2,
                    "avg_position_size": 18034.799,
                    "avg_wallet_inv_size": 18034.799,
                    "sharpe_ratio": 22.105,
                    "annual_vol": 390.451,
                    "flash_num_0": 0,
                    "flash_num_1": 0,
                    "flash_volume_0": 0.0,
                    "flash_volume_1": 0.0,
                    "num_swaps_0": 43,
                    "num_swaps_1": 26,
                    "num_mints": 1,
                    "num_burns": 1,
                    "burns_0": 0.0,
                    "burns_1": 0.0,
                    "mints_0": 1030.862,
                    "mints_1": 1279.317,
                    "num_liquidity_events": 2,
                    "liquidity_change_percent": 18.12307474967476,
                    "open_reserve_0": 12416155973246.258,
                    "close_reserve_0": 12119854868467.383,
                    "open_reserve_1": 8.414,
                    "close_reserve_1": 9.839,
                    "open_reserve_0_base_curr": 15333.754,
                    "open_reserve_1_base_curr": 15201.853,
                    "close_reserve_0_base_curr": 18088.66,
                    "close_reserve_1_base_curr": 17980.938,
                    "poolsize": 36069.598,
                    "open_poolsize": 30535.607,
                    "close_poolsize": 36069.598,
                    "avg_daily_tvl": 818849.284,
                    "avg_daily_vol_tvl_ratio": 101.831,
                    "open_price_0": 1.235e-09,
                    "open_price_1": 1806.742,
                    "high_price_0": 2.05e-09,
                    "high_price_1": 1842.251,
                    "low_price_0": 1.124e-09,
                    "low_price_1": 1806.444,
                    "close_price_0": 1.492e-09,
                    "close_price_1": 1827.596,
                    "all_time_high_0": 3.037e-09,
                    "all_time_high_1": 4864.661,
                    "hours_since_ath_0": 471.0,
                    "hours_since_ath_1": 12164.0,
                    "last_processed3": "2023-04-01T14:28:40.540111",
                    "processed_timestamp_utc": "2023-04-01T14:27:58.217976",
                    "lp_favorite": "false"
                },
            ]
        )],
        responses={
            200: lpV3Serializer,
            400: OpenApiResponse(description='Bad request'),
            401: OpenApiResponse(description="You must be logged in."),
        },
    )
    def get(self, request, *args, **kwargs):
        param = self.kwargs.get('pk')
        param2 = self.kwargs.get('sk')
        param3 = self.kwargs.get('ek')
        legacy = False

        try:
            sort_options = {
                "apy": "-total_apy",
                "tpr": "-total_period_return",
                "fees": "-fees_apy",
                "fee": "-fees_apy",
                "yff": "-yield_on_lp_fees",
                "pcr": "-price_change_ret",
                "hodl": "-hodl_return",
                "hod": "-hodl_return",
                "size": "-poolsize",
                "siz": "-poolsize",
                "ill": "-impermanent_loss_level",
                "imm": "-impermanent_loss_impact",
                "vol": "-volume",
                "trans": "-transactions_period",
                "tra": "-transactions_period",
                "hvl": "hvl",
                "per": "per",
                "new": "recent",
                "favorites": "favorites",
                "portfolio": "portfolio"
            }

            sort_by = sort_options.get(param.lower(), "Other")
            if sort_by == "Other":
                return Response(f'Invalid sorting option: {param}', status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(f'Invalid sorting option: {param}', status=status.HTTP_400_BAD_REQUEST)

        # param2: number of pools, up to 100
        try:
            param2 = int(param2)

        except Exception as e:
            return Response(f'Parameter must be a integer. Received: {param2}', status=status.HTTP_400_BAD_REQUEST)

        if (sort_by != "portfolio" and sort_by != "watchlist") and param2 > 100:
            return Response(f'Parameter can not be greater than 100. Received: {param2}',
                            status=status.HTTP_400_BAD_REQUEST)

        # param 3: time period in days: 1 = 1 Day, 7 = 1 week
        try:
            data_frequency_options = {
                "1": "t1d",
                "7": "t7d",
                "30": "t30",
                "31": "M",
                "90": "tq",
                "365": "t12"
            }
            data_frequency = data_frequency_options.get(param3, 0)

            if data_frequency == 0:
                return Response(f'Invalid time period. Received: {param3}. Check documentation for valid parameters.',
                                status=status.HTTP_400_BAD_REQUEST)
            # ToDo: Check subscription level

        except Exception as e:
            return Response(f'Invalid time period. Received: {param3}. Check documentation for valid parameters.',
                            status=status.HTTP_400_BAD_REQUEST)

        if sort_by == "portfolio" or sort_by == "watchlist":
            try:
                portfolio_requested = UserLpList.objects.using('default').get(id=param2)
                if portfolio_requested.user != request.user:
                    return Response(f'Unauthorized Access. User does not have access to {sort_by}: {param2}',
                                    status=status.HTTP_400_BAD_REQUEST)
            except UserLpList.DoesNotExist:
                return Response(f'Invalid {sort_by} number. Received: {param2}', status=status.HTTP_400_BAD_REQUEST)

        # print("class lp_by sort order:", sort_by)
        top_lp_list = get_lp_list3(username=request.user, lp_cnt=param2, data_frequency=data_frequency, option=sort_by)
        # print(top_lp_list)
        if len(top_lp_list) == 0:
            return Response(f'Unable to find any active assets. Please adjust filters.',
                            status=status.HTTP_204_NO_CONTENT)

        try:
            favoriteLpIds = []
            try:
                # compute favorite list, this will make sure we only query once instead of querying per lpV3Serializer
                favoriteLpList = UserLpList.objects.using('default').get(lp_list_name="Favorites",
                                                                              user_id=request.user)
                LpLists = LpList.objects.using('default').filter(lp_list=favoriteLpList.id)
                for Lp in LpLists:
                    if (Lp.liquidity_pool is not None):
                        favoriteLpIds.append(Lp.liquidity_pool.id)

            except UserLpList.DoesNotExist:
                pass

            serializer = lpV3Serializer(top_lp_list, many=True,
                                        context={'favoriteLpIds': favoriteLpIds})  # serializers.Serializer
        except Exception as e:
            traceback.print_exc()
            print(f"{e}")
            return Response(f'Something went wrong. {e}', status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data)


###############################################################
# GET LIQUIDITY POOL LIST v3
# API for /lp/ - Used to fill table on Liquidity Pool screen
###############################################################
@extend_schema(exclude=True)
def get_lp_list3(username, lp_cnt=20, data_frequency="t1d", option="-total_apy", lp_ids=None):
    # Turn off debug
    debug = False
    sort_by = option

    # Can be used for debugging
    # user_filters = None

    summary_type = SummaryType.objects.using('default').get(data_frequency=data_frequency)

    ##################################################################
    # Liquidity Pool Filters
    collateral_list = []
    use_collateral_filter = True
    min_transactions_period = 0  # Need a default for anonymous users
    try:
        user_filters = get_filters(username)
        if option == "search" or option == "favorites" or option == "portfolio" or option == "watchlist":
            sort_by = '-total_period_return'
            use_collateral_filter = False
        else:
            # Anonymous Users will throw an exception on the next line, which turns off the collateral filters
            current_filter = UserFilters.objects.using('default').get(user=username)

            if debug:
                print(username)
                print(current_filter.collateral_fiat)

            if current_filter.collateral_fiat:
                collateral_list.append(1)
            if current_filter.collateral_crypto:
                collateral_list.append(2)
            if current_filter.collateral_algorithmic:
                collateral_list.append(3)
            if current_filter.collateral_metals:
                collateral_list.append(4)
            if current_filter.collateral_other:
                collateral_list.append(5)

            # If every token is allowed, turn off the collateral filter for speed
            if len(collateral_list) == 5:
                use_collateral_filter = False

            # if debug:
            #   print("collateral_list", collateral_list)

            # Use the minimum weekly for any period grater than a day
            if data_frequency == "t1d":
                min_transactions_period = current_filter.transactions_min_day
            else:
                min_transactions_period = current_filter.transactions_min_week

    except Exception as e:
        if debug:
            print(e)

        use_collateral_filter = False
    ##################################################################

    if debug:
        print(user_filters)

    # print("option=", option)
    # print("lp_ids=", type(lp_ids))
    # If it's not a list or a numpy array, it was an error code, make it an empty list
    if not (isinstance(lp_ids, list) or isinstance(lp_ids, np.ndarray)):
        lp_ids = []

    # Note: filters DO NOT APPLY to Lists such as Favorites
    if option == "favorites":  # Get this user's favorites
        favorites_list = UserLpList.objects.using('default').get(user=username, lp_list_name="Favorites")
        lp_ids = list(LpList.objects.using('default').filter(lp_list=favorites_list,
                                                             liquidity_pool__isnull=False).values_list(
            'liquidity_pool_id', flat=True))
        lp_cnt = len(lp_ids)
    elif option == "portfolio" or option == "watchlist":
        try:
            # Try getting all the lp_ids in the list number passed, lp_cnt is used differently in this case
            lp_ids = list(
                LpList.objects.using('default').filter(lp_list=lp_cnt, liquidity_pool__isnull=False).values_list(
                    'liquidity_pool_id', flat=True))
            # lp_cnt = len(lp_ids)
        except Exception as e:
            print(e)

    # Note: filters DO NOT APPLY to Lists such as Favorites
    if option == "search" or option == "favorites" or option == "portfolio" or option == "watchlist":
        sort_by = '-total_period_return'
        use_collateral_filter = False
        if lp_cnt > 0:
            # print(lp_ids)
            lp_list = LpRecent.objects.using('default').filter(summary_type=summary_type,
                                                               liquidity_pool_id__in=lp_ids).order_by(sort_by)
            # If no liquidity pools are found, return empty
            if len(lp_list) == 0:
                return []
        else:
            return []

    # Filters are turned off for this user
    elif user_filters.use_filters is False:
        use_collateral_filter = False
        lp_list = LpRecent.objects.using('default').filter(summary_type=summary_type)  # Sort happens below

    # Filters are on
    else:
        lp_list = LpRecent.objects.using('default').filter(summary_type=summary_type.id,
                                                           poolsize__gte=user_filters.poolsize_min,
                                                           poolsize__lte=user_filters.poolsize_max,
                                                           volume__gte=user_filters.volume_min,
                                                           volume__lte=user_filters.volume_max,
                                                           impermanent_loss_level__gte=user_filters.ill_min,
                                                           impermanent_loss_level__lte=user_filters.ill_max,
                                                           yield_on_lp_fees__gte=user_filters.yff_min,
                                                           transactions_period__gte=min_transactions_period,
                                                           )

    if option == "recent":  # Get recently added liquidity pools
        sort_by = '-created_at_timestamp_utc'

    if option == "hvl":
        if lp_list is not None:
            # Further filter the return by selecting pools with more volume than poolsize
            lp_list = lp_list.filter(poolsize__lt=F('volume')).order_by('-volume')

    elif option == "per":
        if lp_list is not None:
            # Further filter the return by selecting pools with more volume than poolsize
            lp_list = lp_list.filter(hodl_return__lt=F('total_period_return')).order_by('-total_period_return')

    # Order by the option passed or the default
    else:
        lp_list = lp_list.order_by(sort_by)

    if debug:
        print("LPs found before collateral filter applied:", len(lp_list))

    # Used for API Search
    # print(summary_type)
    top_lp_list = list(lp_list)

    if use_collateral_filter:
        lp_list_index = 0
        new_lp_list = []

        # Go through results and remove any pools containing collateral the user prefers to hide
        for lp_result in top_lp_list:
            if debug:
                print(f"Checking collateral: {lp_result.token0_collateral}-{lp_result.token1_collateral}")
            if ((lp_result.token0_collateral in collateral_list) and (
                    lp_result.token1_collateral in collateral_list)):
                new_lp_list.append(lp_result)  # Add to a list
                if debug:
                    print(f"Keeping: {lp_result.token0_symbol}-{lp_result.token1_symbol}")
                if len(new_lp_list) == lp_cnt:  # Stop processing as soon as there is enough data
                    break
            lp_list_index += 1
        top_lp_list = list(new_lp_list)

    if debug:
        print("LPs returned:", len(top_lp_list))
        print("LPs requested:", lp_cnt)

    top_lp_list = top_lp_list[:lp_cnt]  # Limit response to what was requested

    return top_lp_list

