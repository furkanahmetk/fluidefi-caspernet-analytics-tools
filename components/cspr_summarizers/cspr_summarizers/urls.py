"""cspr_summarizers URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from . import views
from django.views.generic import TemplateView

from cspr_summarizers.api_published import UserAuthentication, Logout, \
    get_user_list, portfolio_model_asset

from liquidity_pools.api.lp_api_views import *
from filters.api.filters import *
from search.api.search_api_calls import *

from .swagger_schema import SpectacularNoShowAPIView, SpectacularRapiDocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/', SpectacularNoShowAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularRapiDocView.as_view(url_name='schema'), name='rapidoc'),
    re_path(r'^auth/$', UserAuthentication.as_view(), name='Authenticate User'),
    re_path(r'^logout/', Logout.as_view(), name='User Logout'),
    re_path(r'^lp/(?P<pk>[\w\-\.]+)/(?P<sk>[\w\-\.]+)/(?P<ek>[\w\-\.]+)/$', lp_by.as_view(),
            name='Get list of liquidity pools sorted by parameter'),
    re_path(r'^search_lp/(?P<pk>[\w\-\.]+)/(?P<sk>[\w\-\.]+)/(?P<ek>[\w\-\.]+)/$', search_lp.as_view(),
            name='Search liquidity pools for term provided'),
    re_path(r'^filters/$', get_user_filters.as_view(), name='get saved filters'),
    re_path(r'^user_filters_update/$', post_user_filters.as_view(), name='save user filters'),
]
