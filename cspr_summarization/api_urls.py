from django.urls import include, path, re_path

try:
    from ..cspr_summarization.api_views import *
except:
    from cspr_summarization.api_views import *


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include('cspr_summarization.page_urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^lp/(?P<pk>[\w\-\.]+)/(?P<sk>[\w\-\.]+)/(?P<ek>[\w\-\.]+)/$', lp_by.as_view(), name='Get list of liquidity pools sorted by parameter'),
    re_path(r'^search_lp/(?P<pk>[\w\-\.]+)/(?P<sk>[\w\-\.]+)/(?P<ek>[\w\-\.]+)/$', search_lp.as_view(), name='Search liquidity pools for term provided'),
    re_path(r'^alerts/$', UserAlertAPIView.as_view(), name='get saved alerts'),
    re_path(r'^swap/', SwapAPIView.as_view(), name="Swap"),
    re_path(r'^add_liquidity/', AddLiquidityAPIView.as_view(), name='Add Liquidity'),
    re_path(r'^remove_liquidity/', RemoveLiquidityAPIView.as_view(), name='Remove Liquidity'),

]