from datetime import datetime, timedelta

from cspr_summarization.entities.LpList import LpList
from cspr_summarization.entities.UserLpList import UserLpList
from cspr_summarizers.serializers import SimpleModelDataSerializerV2, UserFiltersSerializer, SimplePortfolioModelSerializer

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample

###############################################################
# User Authentication
# /auth/
###############################################################
class UserAuthentication(ObtainAuthToken):

    @extend_schema(
        summary="Authenticate",
        description="Gets a token. New tokens are generated every 10 minutes. Calling /auth/ will delete any "
                    "previously issued tokens.",
        request=ObtainAuthToken.serializer_class,
        parameters=[
            OpenApiParameter(
                name='Date: Sun, 23 May 2021 20:42:46 GMT',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='Server: WSGIServer/0.2 CPython/3.9.1',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='Content-Type: application/json',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='Allow: POST, OPTIONS',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='X-Frame-Options: DENY',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='Content-Length: 42',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='Vary: Cookie',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='X-Content-Type-Options: nosniff',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
            OpenApiParameter(
                name='Referrer-Policy: same-origin',
                location=OpenApiParameter.HEADER,
                response=True,
            ),
        ],
        tags=["Access Control"],
        extensions={
            'x-code-samples': [
                {'lang': 'bash', 'label': 'Authenticate',
                 'source': '''curl --location -g --request POST '{{host}}/auth/' 
                    --form 'username="{{UserName}}"'
                    --form 'password="{{UserPassword}}"' 
                    '''
                 },
            ],
        },
        responses={
            200: OpenApiResponse(description="Token in string format wrapped in parenthesis"),
            403: OpenApiResponse(description="<ol><li>Unable to log in with credentials provided. "
                                             "Contact support@fluidefi.com for help.</li></ol>"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        try:
            if serializer.is_valid():
                user = serializer.validated_data['user']
                token, created = Token.objects.using('default').get_or_create(user=user)

                # If a new token was not created, then make a new one if the token is more than 1 hour old
                utc_now = datetime.utcnow()
                if not created and token.created < utc_now - timedelta(minutes=1440):
                    token.delete()
                    token = Token.objects.using('default').create(user=user)

                return Response(token.key)
            else:
                return Response(f'Unable to log in with credentials provided. Contact support@fluidefi.com for help.',
                                status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            # print(e)
            return Response(f'Unable to log in with credentials provided. Contact support@fluidefi.com for help.',
                            status=status.HTTP_403_FORBIDDEN)


class Logout(APIView):
    @extend_schema(
        summary="Logout",
        description="Logs user out and deletes authentication token",
        tags=["Access Control"],
    )
    def get(self, request):
        # simply delete the token to force a login
        try:
            request.user.auth_token.delete()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f'{e}', status=status.HTTP_400_BAD_REQUEST)


# Get the assets in the user list
class get_user_list(APIView):

    @extend_schema(
        summary="Portfolio Model Asset",
        description="Get the assets in the user List",
        tags=["Portfolio Model"],
    )
    def get(self, request, *args, **kwargs):
        param = self.kwargs.get('pk')

        try:
            if param.lower() == "favorites":
                cur_list = UserLpList.objects.using('default').get(user=request.user, lp_list_name="Favorites")
                list_num = cur_list.id
            else:
                list_num = int(param)  # If it's not a number, this will create an exception
                # validate that this user has access to the list number requested
                cur_list = UserLpList.objects.using('default').get(user=request.user, id=list_num)

            user_list = LpList.objects.using('default').filter(lp_list=list_num)
            serializer = SimplePortfolioModelSerializer(user_list, many=True)
            return Response(serializer.data)


        except UserLpList.DoesNotExist:
            return Response(f'Invalid number: {param}', status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(f'Invalid number: {param}', status=status.HTTP_400_BAD_REQUEST)



#######################################################################################################################
# GET Portfolio Model Asset
# API call /portfolio_model_update/ - Add or remove assets to/from a portfolio model.
#######################################################################################################################
class portfolio_model_asset(APIView):
    @extend_schema(
        summary="GET Portfolio Model Asset",
        description="Retrieve the Portfolio Model Asset.",
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
                type=int,
                location=OpenApiParameter.PATH,
                required=True,
                description="Primary Key for the Portfolio Model."
            ),
            OpenApiParameter(
                name='sk',
                type=int,
                location=OpenApiParameter.PATH,
                required=True,
                description="Primary Key for the Portfolio Model Asset."
            ),
        ],
        tags=["Portfolio Model"],
        extensions={
            'x-code-samples': [
                {'lang': 'bash', 'label': 'Example', 'source': '''
                 curl --location --request GET 'http://127.0.0.1:8000/portfolio_model_asset/676/868/' '''
                 },
            ],
        },
        examples=[OpenApiExample(
            name="Response",
            response_only=True,
            value=[
                {'lp_list': 999,
                 'liquidity_pool': 999,
                 'contract_address': '0xB20bd5D04BE54f870D5C0d3cA85d82b34B836405',
                 'currency': 'null',
                 'lp_amount': 27500,
                 'token_address': 'null',
                 'token_amount': 0,
                 'weight': 0.25,
                 'lp_name': 'DAI-USDT',
                 'currency_name': 'null'}
            ]
        )],
        responses={
            200: SimpleModelDataSerializerV2,
            400: OpenApiResponse(description='Bad request'),
            401: OpenApiResponse(description="You must be logged in."),
        }
    )
    def get(self, request, *args, **kwargs):

        # Coming in Milestone 4

        return Response(status=status.HTTP_200_OK)


#######################################################################################################################
# Portfolio Model Update
# API call /portfolio_model_update/ - Add or remove assets to/from a portfolio model.
#######################################################################################################################
class portfolio_model_edit(APIView):
    """
    Portfolio Model Edit
    """

    @extend_schema(
        summary="Portfolio Model Update",
        description="Add or Update a Portfolio Model. Name, Investment Size, Investment Start Timestamp, "
                    "Investment End Timestamp, Currency."
                    "<br><strong>Note that Delete/Clone/Share are not yet implemented.</strong>",
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
                name='data',
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="{<br>"
                            "   'id': 999, <br>"
                            "   'action': 'editmodel', <br>"
                            "   'lp_list_name': 'High Performance Model', <br>"
                            "   'investment_size': 100000.01, <br>"
                            "   'investment_timestamp_utc': '2021-08-01 00:00:00', <br>"
                            "   'investment_end_timestamp_utc': '2022-02-14 14:33:00', <br>"
                            "   'currency_code': 'USD', <br>"
                            "}"
            ),
        ],
        tags=["Portfolio Model"],
        extensions={
            'x-badges': [
                {'color': 'blue', 'label': 'Beta'},
            ],
            #     'x-code-samples': [
            #         {'lang': 'bash', 'label': 'Example', 'source': '''
            #          curl --location --request POST 'http://127.0.0.1:8000/portfolio_update_edit/262/' '''
            #          },
            #     ],
        },
        responses={
            200: OpenApiResponse(description="Ok"),
            400: OpenApiResponse(description='<ul><li>Bad request</li>'
                                             '<li>JSON Payload data payload with a list of errors if any.</li></ul>'),
            401: OpenApiResponse(description="You must be logged in."),
        },
    )
    def post(self, request):
        # Coming in Milestone 4

        return Response(status=status.HTTP_200_OK)
