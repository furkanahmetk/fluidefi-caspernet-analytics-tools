from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer, OpenApiExample
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.urls import resolve, Resolver404

import re               # This is regex & needed for security of text field in API
import numpy as np

import traceback
from pathlib import Path
import os
import sys

cwd = os.getcwd()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(BASE_DIR)
sys.path.append(str(BASE_DIR))

from cspr_summarization.entities.LiquidityPool import LiquidityPool
from cspr_summarizers.serializers import lpV3Serializer
from liquidity_pools.api.lp_api_views import get_lp_list3

#######################################################################################################################
# SEARCH FOR LIQUIDITY POOL; Used in Public API
# /search_lp/
# param 1: string to search for. Can be contract address, lp with '-', or alphanumeric characters (no symbols now)
# param 2: number of pools, up to 100
# param 3: time period in days: 1 = 1 Day, 7 = 1 week
# Results are sorted alphabetically
# examples:
# /search_lp/USDT/20/7/ <= Returns 20 weekly data for 20 lps that contain USDT in name
# /search_lp/USDT-DAI/20/7/ <= It will flip pairs and return DAI-USDT
# /search_lp/0x888759CB22cEDaDF2cFb0049b03309D45aa380D9/40/7/ <= Returns ARMOR-WBTC 7 days results
# /search_lp/btc/10/7/ <= Returns 10 lps with BTC 7 days results
# Test cases for search on Casper net
# /search_lp/e6b4a934630aee279665c99dc2bf4219872b7178990cd7fee7634a0f1362b591/2/1/
# /search_lp/WETH-CSX/1/30/
# /search_lp/WCSPR/3/7/ <= Returns 3 lps with BTC 7 days results
###############################################################
class search_lp(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Search for a Liquidity Pool",
        description="Search for one or more liquidity pools matching the string or " + \
                    "smart contract address provided. " + \
                    "This call is designed to compare liquidity pool performance across DEXes & chains. " + \
                    "It returns one or more entries along with the performance for the time period requested.<br/>" + \
                    "For example: searching for <em>USDC-WETH</em> will return all liquidity pools so they can " + \
                    "be compared. Responses sorted alphabetically by liquidity pool name (not by any metric).<br/>" + \
                    "Tokens in liquidity pool names may be returned in the reverse order of what was entered.<br/>" + \
                    "For example, searching for <em>USDC-DAI</em> will return <em>DAI-USDC</em> because it is " + \
                    "minted this way in the name of the smart contract on the blockchain.",
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
                description="search_string: May be contract address, liquidity pool with dash '-', or " + \
                            "alphanumeric characters (no symbols or special characters accepted)."
            ),
            OpenApiParameter(
                name='sk',
                type=int,
                location=OpenApiParameter.PATH,
                required=True,
                description="num_results: Maximum number of responses to return up to 100. "
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
        tags=["Search"],
        responses={
            200: lpV3Serializer,
            401: OpenApiResponse(description="You must be logged in.")
        },
    )

    def get(self, request, *args, **kwargs):
        param = self.kwargs.get('pk')
        param2 = self.kwargs.get('sk')
        param3 = self.kwargs.get('ek')

        # Validate param2 before searching DB: number of pools, up to 100
        try:
            param2 = int(param2)
        except Exception as e:
            print(e)
            return Response(f'Parameter must be a integer. Received: {param2}', status=status.HTTP_400_BAD_REQUEST)

        if param2 > 100:
            return Response(f'Parameter can not be greater than 100. Received: {param2}',
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate param3 before searching DB: time period in days: 1 = 1 Day, 7 = 1 week
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

        except Exception as e:
            return Response(f'Invalid time period. Received: {param3}. Check documentation for valid parameters.',
                            status=status.HTTP_400_BAD_REQUEST)

        param = param.strip()  # Strip any leading and trailing spaces
        param = param.replace('__', ' ')  # replace __ with a space
        lp_ids = []

        if len(param) > 100:
            return Response(f'Search term must be less than 101 characters. Received: {param}',
                            status=status.HTTP_400_BAD_REQUEST)
        elif param.find('%') >= 0:
            return Response(f'Search term cannot contain % characters. Received: {param}',
                            status=status.HTTP_400_BAD_REQUEST)

        # First, get a list of liquidity pools using below
        lp_ids = search_lps(param)
        print(f"{param} found {lp_ids}")

        # Did not find any pools, check for dead ones
        if lp_ids is None:
            lp_ids = list(LiquidityPool.objects.using('default').
                          filter(lp_watchlevel__gte=0,
                                 name__icontains=param).values_list('id', flat=True))
            if lp_ids is None:
                return Response(f'Unable to find any liquidity pools using: {param}', status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(f'Liquidity pools using: {param} are all inactive',
                                status=status.HTTP_204_NO_CONTENT)

        # Go get results
        results_list = get_lp_list3(username=request.user, lp_cnt=param2, data_frequency=data_frequency,
                                    option="search", lp_ids=lp_ids)
        print(results_list)

        if len(results_list) == 0:
            try:
                resolver = resolve(request.path_info)

            except Resolver404 as ex:
                return Response(f'Liquidity pool found, but no summary data: {param}',
                                status=status.HTTP_204_NO_CONTENT)

        # Serialize the results
        serializer = lpV3Serializer(results_list, many=True)

        return Response(serializer.data)


@extend_schema(exclude=True)
def search_lps(search_string=""):
    # Validate & retrieve Liquidity Pool requested
    lp_ids = []
    try:
        # search by contract address - get only 1
        if len(search_string) == 64:
            # Search for non-hex characters so it doesn't break Web3.to_checksum_address
            regex = re.compile('[@!#$%^&*()<>?/\|}{~:]GgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz')
            if regex.search(search_string[2:]) is None:
                try:
                    lp_contract_address = search_string
                    # print(lp_contract_address)
                    lp_object = LiquidityPool.objects.using('default').get(contract_address=lp_contract_address)
                    lp_ids.append(lp_object.id)
                except LiquidityPool.DoesNotExist:  # Did not find liquidity pool in the platform requested
                    pass

                if len(lp_ids) == 0:
                    try:
                        lp_object = LiquidityPool.objects.using('default').get(contract_address=lp_contract_address)
                        lp_ids.append(lp_object.id)
                    except LiquidityPool.DoesNotExist:  # Did not find liquidity pool in the platform requested
                        # print("Searching for address in tokens ", lp_contract_address)
                        lp_ids_t0 = list(
                            LiquidityPool.objects.using('default').filter(lp_watchlevel__gte=1,
                                                                               token0_address=lp_contract_address).values_list(
                                'id', flat=True))
                        lp_ids_t1 = list(
                            LiquidityPool.objects.using('default').filter(lp_watchlevel__gte=1,
                                                                               token1_address=lp_contract_address).values_list(
                                'id', flat=True))
                        lp_ids = np.unique(lp_ids_t0 + lp_ids_t1)  # Using Numpy to find unique IDs
                        if len(lp_ids) == 0:
                            return Response(f'Unable to find any active liquidity pools using: {search_string}',
                                            status=status.HTTP_204_NO_CONTENT)

        if len(lp_ids) == 0 and search_string.find('-') >= 0:  # There is a split in the name
            try:
                # 1st) Try for exact match
                # print("1st) Try for exact match")
                exact_lp_ids = list(
                    LiquidityPool.objects.using('default').filter(name__icontains=search_string).values_list('id', flat=True))
                # print("Exact:", exact_lp_ids)
                # 2nd) Try pair names reversed
                # print("2nd) Try pair names reversed")
                search_string_flip = search_string.split("-")[1] + "-" + search_string.split("-")[0]
                reversed_lp_ids = list(
                    LiquidityPool.objects.using('default').filter(name__icontains=search_string_flip).values_list(
                        'id', flat=True))
                lp_ids = np.unique(exact_lp_ids + reversed_lp_ids)
                # print("reversed:", reversed_lp_ids)
                # print("SEARCH FOUND: ", len(lp_ids))

            except LiquidityPool.DoesNotExist:
                print("Exception searching")

        if len(lp_ids) == 0 and (
                search_string.find('-') >= 0 or search_string.find('_') >= 0):  # 3rd) Go broad & look for each token
            # print("3rd) Go broad & look for each token")
            try:
                if search_string.find('-') >= 0:
                    token0_search = search_string.split("-")[0]
                    token1_search = search_string.split("-")[1]
                elif search_string.find('_') >= 0:
                    token0_search = search_string.split("_")[0]
                    token1_search = search_string.split("_")[1]

                lp_ids_t0 = list(
                    LiquidityPool.objects.using('default').filter(lp_watchlevel__gte=1,
                                                                       name__icontains=token0_search).values_list(
                        'id', flat=True))
                lp_ids_t1 = list(
                    LiquidityPool.objects.using('default').filter(lp_watchlevel__gte=1,
                                                                       name__icontains=token1_search).values_list(
                        'id', flat=True))
                lp_ids = np.unique(lp_ids_t0 + lp_ids_t1)

            except LiquidityPool.DoesNotExist:
                return Response(f'Unable to find liquidity pool requested: {search_string} or {search_string_flip}',
                                status=status.HTTP_204_NO_CONTENT)

        elif len(lp_ids) == 0:
            # Find the requested Liquidity Pool using case-insensitive search
            # print("case-insensitive search: ", search_string)
            lp_ids = list(LiquidityPool.objects.using('default').filter(lp_watchlevel__gte=1,
                                                                             name__icontains=search_string).values_list(
                'id', flat=True))

        # print("RETURNING: ", len(lp_ids))
        return lp_ids

    except LiquidityPool.DoesNotExist:  # Did not find liquidity pool in the platform requested
        return Response(f'Unable to find any active liquidity pools using: {search_string}',
                        status=status.HTTP_204_NO_CONTENT)
