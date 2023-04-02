# from .api_published import get_lp_list3
from liquidity_pools.api.lp_api_views import *
from django.shortcuts import render


def index(request):
        trending_pools = get_lp_list3(request.user, lp_cnt=10, data_frequency="t1d", option="-total_apy")

        context = {
            'trending_pools': trending_pools
        }

        return render(request, 'index.html', context=context)