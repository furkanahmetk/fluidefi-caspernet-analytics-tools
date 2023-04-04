# Used by API call above, views.py (homepage and lp screens)
from cspr_summarization.entities.UserFilters import UserFilters


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
