from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from cspr_summarization.entities.UserFilters import UserFilters
from cspr_summarization.entities.LpList import LpList
from cspr_summarization.entities.UserLpList import UserLpList

class SimpleModelDataSerializerV2(serializers.ModelSerializer):
    lp_name = serializers.CharField(source='liquidity_pool.name', allow_null=True, read_only=True)
    currency_name = serializers.CharField(source='currency.full_name', allow_null=True, read_only=True)
    platform_name = serializers.CharField(source='liquidity_pool.platform.name', allow_null=True, read_only=True)

    class Meta:
        model = LpList
        fields = ('lp_list', 'liquidity_pool', 'contract_address', 'currency', 'lp_amount', 'token_address',
                  'token_amount', 'weight', 'lp_name', 'currency_name', 'platform_name')


#######################################################################################################################
# Serializer used by /lp/ to return the summary information for top performing pools
#######################################################################################################################
class lpV3Serializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    id = serializers.IntegerField(read_only=True, required=False)
    liquidity_pool_id = serializers.IntegerField(read_only=True, required=False)
    lp_name = serializers.CharField(max_length=100, read_only=True, required=False)
    open_timestamp_utc = serializers.DateTimeField(read_only=True, required=False)
    close_timestamp_utc = serializers.DateTimeField(read_only=True, required=False)
    # platform = serializers.CharField(read_only=True, required=False)
    platform_id = serializers.CharField(read_only=True, required=False)
    platform_name = serializers.CharField(read_only=True, required=False)
    fee_taken = serializers.FloatField(read_only=True, required=False, allow_null=True)
    fee_earned = serializers.FloatField(read_only=True, required=False, allow_null=True)
    contract_address = serializers.CharField(max_length=100, read_only=True, required=False)
    url = serializers.CharField(max_length=255, read_only=True, required=False)
    created_at_timestamp_utc = serializers.DateTimeField(read_only=True, required=False)
    token0_symbol = serializers.CharField(max_length=12, read_only=True, required=False)
    token1_symbol = serializers.CharField(max_length=12, read_only=True, required=False)
    token0_address = serializers.CharField(max_length=100, read_only=True, required=False)
    token1_address = serializers.CharField(max_length=100, read_only=True, required=False)
    token0_collateral = serializers.CharField(read_only=True, required=False)
    token1_collateral = serializers.CharField(read_only=True, required=False)
    total_period_return = serializers.FloatField(read_only=True, required=False, allow_null=True)
    total_apy = serializers.FloatField(read_only=True, required=False, allow_null=True)
    yield_on_lp_fees = serializers.FloatField(read_only=True, required=False, allow_null=True)
    fees_apy = serializers.FloatField(read_only=True, required=False, allow_null=True)
    price_change_ret = serializers.FloatField(read_only=True, required=False, allow_null=True)
    misc_return = serializers.FloatField(read_only=True, required=False, allow_null=True)
    hodl_return = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_lp_token_price = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_lp_token_price = serializers.FloatField(read_only=True, required=False, allow_null=True)
    token_0_price_return = serializers.FloatField(read_only=True, required=False, allow_null=True)
    token_1_price_return = serializers.FloatField(read_only=True, required=False, allow_null=True)
    impermanent_loss_level = serializers.FloatField(read_only=True, required=False, allow_null=True)
    impermanent_loss_impact = serializers.FloatField(read_only=True, required=False, allow_null=True)
    volume_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    volume_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    volume_0_base_curr = serializers.FloatField(read_only=True, required=False, allow_null=True)
    volume_1_base_curr = serializers.FloatField(read_only=True, required=False, allow_null=True)
    volume = serializers.FloatField(read_only=True, required=False, allow_null=True)
    avg_daily_vol = serializers.FloatField(read_only=True, required=False, allow_null=True)
    transactions_period = serializers.FloatField(read_only=True, required=False, allow_null=True)
    num_swaps = serializers.IntegerField(read_only=True, required=False)
    avg_swap_size = serializers.FloatField(read_only=True, required=False, allow_null=True)
    active_positions = serializers.IntegerField(read_only=True, required=False)
    active_wallets = serializers.IntegerField(read_only=True, required=False)
    avg_position_size = serializers.FloatField(read_only=True, required=False, allow_null=True)
    avg_wallet_inv_size = serializers.FloatField(read_only=True, required=False, allow_null=True)
    sharpe_ratio = serializers.FloatField(read_only=True, required=False, allow_null=True)
    annual_vol = serializers.FloatField(read_only=True, required=False, allow_null=True)
    flash_num_0 = serializers.IntegerField(read_only=True, required=False)
    flash_num_1 = serializers.IntegerField(read_only=True, required=False)
    flash_volume_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    flash_volume_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    num_swaps_0 = serializers.IntegerField(read_only=True, required=False)
    num_swaps_1 = serializers.IntegerField(read_only=True, required=False)
    num_mints = serializers.IntegerField(read_only=True, required=False)
    num_burns = serializers.IntegerField(read_only=True, required=False)
    burns_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    burns_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    mints_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    mints_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    num_liquidity_events = serializers.IntegerField(read_only=True, required=False)
    liquidity_change_percent = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_reserve_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_reserve_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_reserve_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_reserve_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_reserve_0_base_curr = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_reserve_1_base_curr = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_reserve_0_base_curr = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_reserve_1_base_curr = serializers.FloatField(read_only=True, required=False, allow_null=True)
    poolsize = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_poolsize = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_poolsize = serializers.FloatField(read_only=True, required=False, allow_null=True)
    avg_daily_tvl = serializers.FloatField(read_only=True, required=False, allow_null=True)
    avg_daily_vol_tvl_ratio = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_price_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    open_price_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    high_price_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    high_price_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    low_price_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    low_price_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_price_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    close_price_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    all_time_high_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    all_time_high_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    hours_since_ath_0 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    hours_since_ath_1 = serializers.FloatField(read_only=True, required=False, allow_null=True)
    last_processed3 = serializers.DateTimeField(read_only=True, required=False)
    processed_timestamp_utc = serializers.DateTimeField(read_only=True, required=False)

    lp_favorite = serializers.SerializerMethodField('_isFavorite')

    def _isFavorite(self, obj):
        favoriteLpIds = self.context.get('favoriteLpIds', None)
        if favoriteLpIds:
            return obj.liquidity_pool_id in favoriteLpIds


class UserFiltersSerializer(serializers.ModelSerializer):
    filter_version = serializers.IntegerField(read_only=False, required=True,
                    help_text="Integer of the filter version to use. Example (2)")
    collateral_fiat = serializers.BooleanField(read_only=False, required=True,
                    help_text="true/false - include tokens with fiat backed collateral. Example (USDT, USDC)")
    collateral_crypto = serializers.BooleanField(read_only=False, required=True,
                    help_text="true/false - include tokens with crypto backed collateral. Examples (DAI, sUSD)")
    collateral_algorithmic = serializers.BooleanField(read_only=False, required=True,
                    help_text="true/false - include tokens that use algorithmic rebasing to stabilize price. Example (AMP)")
    collateral_metals = serializers.BooleanField(read_only=False, required=True,
                    help_text="true/false - include tokens with precious metals (gold) backed collateral. Example (GIFT, PAXG)")
    collateral_other = serializers.BooleanField(read_only=False, required=True,
                    help_text="true/false - include tokens with no collateral or some other collateral not included with other parameters.")
    poolsize_min = serializers.IntegerField(read_only=False, required=False,
                    help_text="Value in USD of the minimum poolsize for the period. Example (5000000)")
    poolsize_max = serializers.IntegerField(read_only=False, required=False,
                    help_text="Value in USD of the maximum poolsize for the period. Example (99000000)")
    volume_min = serializers.IntegerField(read_only=False, required=False,
                    help_text="Value in USD of the minimum volume for the period. Example (10000)")
    volume_max = serializers.IntegerField(read_only=False, required=False,
                    help_text="Value in USD of the maximum volume for the period. Example (9900000)")
    ill_min = serializers.FloatField(read_only=False, required=True,
                    help_text="Minimum impermanent loss level for the period. Example (-95.99)")
    ill_max = serializers.FloatField(read_only=False, required=True,
                    help_text="Maximum impermanent loss level for the period. Example (95.0)")
    yff_min = serializers.FloatField(read_only=False, required=True,
                    help_text="Minimum yield from fees for the period. Example (25.0)")
    transactions_min_day = serializers.IntegerField(read_only=False, required=False,
                    help_text="Minimum number of transactions in one day. Example (1)")
    transactions_min_week = serializers.IntegerField(read_only=False, required=False,
                    help_text="Minimum number of transactions in one week. Example (10)")

    class Meta:
        model = UserFilters
        fields = ('filter_version', 'collateral_fiat', 'collateral_crypto', 'collateral_algorithmic',
                  'collateral_metals', 'collateral_other', 'poolsize_min', 'poolsize_max',
                  'volume_min', 'volume_max', 'ill_min', 'ill_max', 'yff_min', 'transactions_min_day',
                  'transactions_min_week', )


class SimplePortfolioModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLpList
        fields = ('id', 'lp_list_name', 'timestamp_utc', 'investment_size', 'investment_timestamp_utc',
                  'investment_end_timestamp_utc', 'currency')