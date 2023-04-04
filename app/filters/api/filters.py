from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from django.urls import resolve, Resolver404

import traceback
from pathlib import Path
import os
import sys

cwd = os.getcwd()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
os.chdir(BASE_DIR)
sys.path.append(str(BASE_DIR))


from cspr_summarization.entities.Platform import Platform
from cspr_summarization.entities.UserFilters import UserFilters
from cspr_summarizers.serializers import UserFiltersSerializer

###############################################################
# User filters
# Used for API call /filters/
###############################################################
class get_user_filters(APIView):

    @extend_schema(
        summary="Filters",
        description="Returns the global filter settings for the current user. How filters work:<br/>" + \
                    "If a liquidity pool has a token that matches one of the filter settings set to true, " + \
                    "then the liquidity pool is included in the response.<br/>" + \
                    "For example: if <em>collateral_fiat:true</em> and <em>collateral_algorithmic:false</em> then " + \
                    "DAI-USDT is included in the response because USDT has a fiat collateral.<br/><br/>" + \
                    "NOTE: filters do NOT apply to search.<br/><br/>" + \
                    "Please refer to section on LIQUIDITY POOL METRICS for more details on each metric.",
        parameters=[
            OpenApiParameter(
                name='Authorization',
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description='{{UserToken}} <br>'
                            '"Token " + token returned during authentication.'
            ),
        ],
        tags=["Filters"],
        responses={
            200: UserFiltersSerializer,
            401: OpenApiResponse(description="You must be logged in.")
        },
    )
    def get(self, request):

        try:
            # print(request.user)
            user_filter = get_filters(username=request.user)
            if user_filter is None:
                return Response(f'Filters error: No filters found.', status=status.HTTP_400_BAD_REQUEST)

            serializer = UserFiltersSerializer(user_filter)
            return Response(serializer.data)

        except Exception as e:
            return Response(f'Unexpected error {e}', status=status.HTTP_400_BAD_REQUEST)

        return Response(f'Not logged in.', status=status.HTTP_400_BAD_REQUEST)


###############################################################
# User filters update
# Used for API call /user_filters_update/
###############################################################
class post_user_filters(APIView):

    @staticmethod
    @extend_schema(
        summary="User Filters Update",
        description="Update the filters that limit the liquidity pools returned. At least one collateral filter " + \
                    "must be True or an error 400 is returned.<br/>" + \
                    "NOTE: filters do NOT apply to search.<br/><br/>" + \
                    "Please refer to section on LIQUIDITY POOL METRICS for more details on each metric.",
        parameters=[
            OpenApiParameter(
                name='Authorization',
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description='{{UserToken}} <br>'
                            '"Token " + token returned during authentication.'
            ),
        ],
        tags=["Filters"],
        responses={
            200: UserFiltersSerializer,
            400: OpenApiResponse(description='Bad request'),
            401: OpenApiResponse(description="You must be logged in.")
        },
    )
    def post(request):
        if request.user is not None:
            if request.method == 'POST':

                try:
                    current_filter = UserFilters.objects.using('default').get(user=request.user)

                    # Validate the data passed. If it is not valid JSON data, an exception is thrown
                    # I (russell) took this out because I could not get it to recognize valid JSON from javascript.
                    # it seems that the Serializer does handle invalid JSON and actually gives a better error message
                    filter_data = JSONParser().parse(request)
                    validate_filter_data = UserFiltersSerializer(data=filter_data)
                    # validate_filter_data = UserFiltersSerializer(data=request.data)
                    if validate_filter_data.is_valid():
                        serializer = UserFiltersSerializer(current_filter, data=request.data)
                    else:
                        return Response(data=validate_filter_data.errors, status=status.HTTP_400_BAD_REQUEST)

                    # If the serializer is valid, save the choices
                    if serializer.is_valid():
                        serializer.save()
                        resave = False

                        ###########################
                        # Validate filter settings
                        # At least one collateral filter must be on or there nothing is returned.
                        # Check the filters that were just saved. If there are no filters on, turn on the fiat & re-save
                        current_filter = UserFilters.objects.using('default').get(user=request.user)
                        if not (current_filter.collateral_fiat or current_filter.collateral_crypto or
                                current_filter.collateral_algorithmic or current_filter.collateral_metals or
                                current_filter.collateral_other):
                            current_filter.collateral_fiat = True
                            resave = True

                        # Check the min and max values
                        if current_filter.poolsize_min < 0:
                            current_filter.poolsize_min = 0
                            resave = True
                        if current_filter.poolsize_min > 2147483647:
                            current_filter.poolsize_min = 2147483647  # 2,147,483,647 max poolsize
                            resave = True
                        if current_filter.poolsize_max < 0:
                            current_filter.poolsize_max = 0
                            resave = True
                        if current_filter.poolsize_max > 2147483647:
                            current_filter.poolsize_max = 2147483647  # 2,147,483,647 max poolsize
                            resave = True
                        if current_filter.poolsize_min >= current_filter.poolsize_max:  # min value cannot exceed max
                            current_filter.poolsize_min = 0
                            resave = True

                        if current_filter.volume_min < 0:
                            current_filter.volume_min = 0
                            resave = True
                        if current_filter.volume_min > 2147483647:
                            current_filter.volume_min = 2147483647  # 2,147,483,647 Max in volume
                            resave = True
                        if current_filter.volume_max < 0:
                            current_filter.volume_max = 0
                            resave = True
                        if current_filter.volume_max > 2147483647:
                            current_filter.volume_max = 2147483647  # 2,147,483,647 Max in volume
                            resave = True
                        if current_filter.volume_min >= current_filter.volume_max:  # min value cannot exceed max
                            current_filter.volume_min = 0
                            resave = True

                        if current_filter.ill_min < -9999.00:
                            current_filter.ill_min = -9999.00
                            resave = True
                        if current_filter.ill_min > 99999.00:
                            current_filter.iil_min = 99999.00
                            resave = True
                        if current_filter.ill_max < 1:
                            current_filter.ill_max = 1
                            resave = True
                        if current_filter.ill_max > 99999.00:
                            current_filter.ill_max = 99999.00
                            resave = True
                        if current_filter.ill_min >= current_filter.ill_max:
                            current_filter.ill_min = .1
                            resave = True

                        if current_filter.yff_min < -9999.00:
                            current_filter.yff_min = -9999.00
                            resave = True
                        if current_filter.yff_min > 99999.00:
                            current_filter.yff_min = 99999.00
                            resave = True

                        if current_filter.transactions_min_day < 0:
                            current_filter.transactions_min_day = 0
                            resave = True
                        if current_filter.transactions_min_day > 100000000:
                            current_filter.transactions_min_day = 100000000  # Max 100 million transactions per day
                            resave = True
                        if current_filter.transactions_min_week < 0:
                            current_filter.transactions_min_week = 0
                            resave = True
                        if current_filter.transactions_min_week > 1000000000:
                            current_filter.transactions_min_week = 1000000000  # Max 1 billion transactions per week
                            resave = True

                        # Platform and network
                        active_platforms = Platform.objects.using('default').filter(fl_supported=True)
                        valid_networks = active_platforms.values_list('network', flat=True).distinct()
                        if current_filter.platform_id > 0:
                            try:
                                platform_selected = active_platforms.get(id=current_filter.platform_id)
                                current_filter.network_id = platform_selected.network.id
                                if current_filter.network_id is None:
                                    current_filter.network_id = 0

                            except Exception as e:
                                return Response(f'Invalid platform # requested. Please check documentation. {e}',
                                                status=status.HTTP_400_BAD_REQUEST)
                            resave = True

                        elif current_filter.network_id != 0 and current_filter.network_id not in valid_networks:
                            return Response(f'Invalid network # requested. Please check documentation.',
                                            status=status.HTTP_400_BAD_REQUEST)
                            resave = True

                        if resave:
                            current_filter.save()
                            serializer = UserFiltersSerializer(current_filter)

                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                    else:
                        try:
                            resolve(request.path_info)
                            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                        except Resolver404 as ex:
                            return Response(f'Invalid API request. {serializer.errors}',
                                            status=status.HTTP_400_BAD_REQUEST)

                except Exception as e:
                    return Response(f'Invalid API request. {e}', status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(f'Invalid API request.', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(f'Invalid API request.', status=status.HTTP_400_BAD_REQUEST)

# Used by the above API cals
@extend_schema(exclude=True)
def get_filters(username):
    try:
        default_filter = create_default_filter()

        try:
            # print("Get filters for username:", username)
            if not username.is_authenticated:
                # print("Returning default filters from default_user_settings")
                return default_filter
            else:
                saved_filter = UserFilters.objects.using('default').get(user=username)
                if saved_filter.filter_version is not None and default_filter.filter_version == saved_filter.filter_version:
                    return saved_filter

            # print("User has an old filter version")

        except UserFilters.DoesNotExist:
            pass
            # print("No filters for this user")

        new_filters = UserFilters.objects.using('default').update_or_create(user=username,
                                                                            defaults={
                                                                                'use_filters': default_filter.use_filters,
                                                                                'filter_version': default_filter.filter_version,
                                                                                'collateral_fiat': default_filter.collateral_fiat,
                                                                                'collateral_crypto': default_filter.collateral_crypto,
                                                                                'collateral_algorithmic': default_filter.collateral_algorithmic,
                                                                                'collateral_metals': default_filter.collateral_metals,
                                                                                'collateral_other': default_filter.collateral_other,
                                                                                'poolsize_min': default_filter.poolsize_min,
                                                                                'poolsize_max': default_filter.poolsize_max,
                                                                                'volume_min': default_filter.volume_min,
                                                                                'volume_max': default_filter.volume_max,
                                                                                'ill_min': default_filter.ill_min,
                                                                                'ill_max': default_filter.ill_max,
                                                                                'yff_min': default_filter.yff_min,
                                                                                'transactions_min_day': default_filter.transactions_min_day,
                                                                                'transactions_min_week': default_filter.transactions_min_week
                                                                            })

        # IMPORTANT: return the first one [0] in the tuple because it is the object
        return new_filters[0]
    except Exception as e:
        print(f'Unexpected error {e}')
        return None


def create_default_filter():
    default_filter = UserFilters()

    default_filter.use_filters = True
    default_filter.filter_version = 1
    default_filter.collateral_fiat = True
    default_filter.collateral_crypto = True
    default_filter.collateral_algorithmic = True
    default_filter.collateral_metals = True
    default_filter.collateral_other = True
    default_filter.poolsize_min = 0
    default_filter.poolsize_max = 9223372036854775807
    default_filter.volume_min = 0
    default_filter.volume_max = 9223372036854775807
    default_filter.ill_min = -9999.0
    default_filter.ill_max = 9999.99
    default_filter.yff_min = -9999.0
    default_filter.transactions_min_day = 0
    default_filter.transactions_min_week = 0
    default_filter.pool_size_t1d_min = None
    default_filter.pool_size_td1_max = None
    default_filter.pool_size_t7d_min = None
    default_filter.pool_size_t7d_max = None
    default_filter.volume_t1d_min = None
    default_filter.volume_t1d_max = None
    default_filter.volume_t7d_min = None
    default_filter.volume_t7d_max = None

    return default_filter
