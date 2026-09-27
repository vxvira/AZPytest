import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from src.analytics.PriceAnalytics import PriceAnalytics

PRICE  = [100, 102, 105, 103, 101, 101, 104.0]
VOLUME = [5, 2, 10, 4, 6, 3, 8.0]

@pytest.fixture
def pa():
    return PriceAnalytics(pd.Series(PRICE), pd.Series(VOLUME))

def series(values): return pd.Series(values, dtype=float)

def test_manipulate_helpers_swap_the_series(pa):
    pa.ManipulatePriceSeries(pa.PriceSeries[:3])
    pa.ManipulateVolumeSeries(pa.VolumeSeries[:3])
    assert len(pa.PriceSeries) == 3 and len(pa.VolumeSeries) == 3

@pytest.mark.parametrize("method", [
    "returnVolumeWeightedAveragePrice",
    "returnOnBalanceVolume",
    "returnVolumeProfile",
    "returnPointOfControl",
    "returnValueArea",
])
def test_volume_indicators_are_fatal_without_a_volume_series(method):
    with pytest.raises(ValueError, match=r"^\[fatal\] VolumeSeries is required"):
        getattr(PriceAnalytics(pd.Series(PRICE)), method)()

def test_exponential_moving_average_matches_the_recursion(pa):
    alpha, expected = 2 / (3 + 1), [PRICE[0]]
    for p in PRICE[1:]: expected.append(alpha * p + (1 - alpha) * expected[-1])
    assert pa.returnExponentialMovingAverage(3).tolist() == pytest.approx(expected)

def test_simple_moving_average(pa):
    result = pa.returnSimpleMovingAveraage(3)
    assert result.isna().tolist() == [True, True, False, False, False, False, False]
    assert result.dropna().tolist() == pytest.approx([(100 + 102 + 105) / 3, (102 + 105 + 103) / 3, 103, (103 + 101 + 101) / 3, 102])

def test_vwap_is_running_price_times_volume_over_running_volume(pa):
    result = pa.returnVolumeWeightedAveragePrice()
    assert result[:3].tolist() == pytest.approx([100, (100 * 5 + 102 * 2) / 7, (100 * 5 + 102 * 2 + 105 * 10) / 17])
    assert result.iloc[-1] == pytest.approx(np.dot(PRICE, VOLUME) / sum(VOLUME))

def test_vwap_ignores_rows_with_missing_data():
    pa = PriceAnalytics(series([100, np.nan, 110]), series([1, 5, 1]))
    assert pa.returnVolumeWeightedAveragePrice().tolist() == pytest.approx([100, 105])

def test_on_balance_volume_adds_up_ticks_subtracts_down_ticks_ignores_flat(pa):
    assert pa.returnOnBalanceVolume().tolist() == [0, 2, 12, 8, 2, 2, 10]

def test_volume_profile_with_bins(pa):
    profile = pa.returnVolumeProfile(bins=4)  # levels 100-101.25, 101.25-102.5, 102.5-103.75, 103.75-105
    assert profile.index.name == "price"
    assert profile.index.tolist() == pytest.approx([100.625, 101.875, 103.125, 104.375])
    assert profile["volume"].tolist() == [14, 2, 4, 18]

def test_volume_profile_with_binSize(pa):
    profile = pa.returnVolumeProfile(binSize=2)  # 100-102, 102-104, 104-106
    assert profile.index.tolist() == [101, 103, 105]
    assert profile["volume"].tolist() == [14, 6, 18]

def test_volume_profile_conserves_total_volume(pa):
    for bins in (1, 3, 10, 50):
        assert pa.returnVolumeProfile(bins=bins)["volume"].sum() == pytest.approx(sum(VOLUME))

def test_volume_profile_of_a_single_price_is_one_level():
    profile = PriceAnalytics(series([5, 5, 5]), series([1, 2, 3])).returnVolumeProfile(bins=3)
    assert profile["volume"].tolist() == [6]
    assert profile.index.tolist() == [5]

def test_volume_profile_skips_rows_with_missing_data():
    profile = PriceAnalytics(series([100, np.nan, 105]), series([1, 2, 3])).returnVolumeProfile(bins=2)
    assert profile["volume"].sum() == 4

def test_point_of_control_is_the_busiest_level(pa):
    assert pa.returnPointOfControl(bins=4) == pytest.approx(104.375)
    assert pa.returnPointOfControl(binSize=2) == 105

def test_value_area_expands_from_the_poc_toward_the_busier_side(pa):
    assert pa.returnValueArea(bins=4) == pytest.approx((100.625, 104.375))                # 70% of 38 needs every level below the POC
    assert pa.returnValueArea(bins=4, pct=0.5) == pytest.approx((103.125, 104.375))       # POC (18) + the 4 below it = 22 >= 19
    assert pa.returnValueArea(bins=4, pct=0.3) == pytest.approx((104.375, 104.375))       # the POC alone covers 30%

def test_value_area_prefers_the_upper_level_on_a_tie():
    # levels 1, 2, 3 hold volume 3, 10, 3: from the POC (2) both neighbours tie, and 80% of 16 is met after one step
    pa = PriceAnalytics(series([1, 2, 3]), series([3, 10, 3]))
    assert pa.returnValueArea(bins=3, pct=0.8) == pytest.approx((2, 2 + 2 / 3))

def test_value_area_returns_plain_floats(pa):
    low, high = pa.returnValueArea(bins=4)
    assert type(low) is float and type(high) is float

def test_bollinger_bands(pa):
    b = pa.returnBollingerBands(period=3, numStd=2)
    assert list(b.columns) == ["middle", "upper", "lower"]
    assert b["middle"].isna().tolist() == [True, True, False, False, False, False, False]
    std = np.std([100, 102, 105])  # population std, like most charting packages
    assert b["middle"].iloc[2] == pytest.approx(np.mean([100, 102, 105]))
    assert b["upper"].iloc[2] == pytest.approx(np.mean([100, 102, 105]) + 2 * std)
    assert b["lower"].iloc[2] == pytest.approx(np.mean([100, 102, 105]) - 2 * std)

def test_bollinger_middle_is_the_simple_moving_average(pa):
    assert_series_equal(pa.returnBollingerBands(3)["middle"], pa.returnSimpleMovingAveraage(3), check_names=False)

def test_bollinger_numStd_scales_the_band_width(pa):
    one, two = pa.returnBollingerBands(3, numStd=1), pa.returnBollingerBands(3, numStd=2)
    assert (two["upper"] - two["middle"]).dropna().tolist() == pytest.approx(((one["upper"] - one["middle"]) * 2).dropna().tolist())

def test_rsi_is_100_when_price_only_rises_and_0_when_it_only_falls():
    up, down = PriceAnalytics(series(range(1, 31))), PriceAnalytics(series(range(30, 0, -1)))
    assert up.returnRelativeStrengthIndex(14).iloc[-1] == 100
    assert down.returnRelativeStrengthIndex(14).iloc[-1] == 0

def test_rsi_matches_wilders_smoothing_by_hand():
    price  = np.random.default_rng(7).normal(0, 1, 60).cumsum() + 100
    period = 5
    alpha  = 1 / period                                    # Wilder smoothing: each new change gets 1/period of the weight
    gain = loss = None
    expected = {}
    for i in range(1, len(price)):
        change = price[i] - price[i - 1]
        g, l = max(change, 0), max(-change, 0)
        gain, loss = (g, l) if gain is None else ((1 - alpha) * gain + alpha * g, (1 - alpha) * loss + alpha * l)
        if i >= period: expected[i] = 100 - 100 / (1 + gain / loss)   # reported once `period` changes have been seen
    result = PriceAnalytics(pd.Series(price)).returnRelativeStrengthIndex(period)
    assert result.dropna().index.tolist() == list(expected)
    assert result.dropna().tolist() == pytest.approx(list(expected.values()))

def test_rsi_needs_a_full_period_before_reporting():
    result = PriceAnalytics(series(range(1, 31))).returnRelativeStrengthIndex(14)
    assert result.isna().sum() == 14

def test_rsi_stays_between_0_and_100_and_is_about_50_when_moves_alternate():
    alternating = PriceAnalytics(series([100 + (i % 2) for i in range(200)])).returnRelativeStrengthIndex(14).dropna()
    assert alternating.between(0, 100).all()
    assert alternating.iloc[-1] == pytest.approx(50, abs=5)

def test_macd_columns_and_definition():
    price = series(100 + np.random.default_rng(0).normal(0, 1, 100).cumsum())
    m = PriceAnalytics(price).returnMACD(fast=12, slow=26, signal=9)
    assert list(m.columns) == ["macd", "signal", "histogram"]
    expected = price.ewm(span=12, adjust=False).mean() - price.ewm(span=26, adjust=False).mean()
    assert m["macd"].tolist() == pytest.approx(expected.tolist())
    assert m["signal"].tolist() == pytest.approx(expected.ewm(span=9, adjust=False).mean().tolist())
    assert m["histogram"].tolist() == pytest.approx((m["macd"] - m["signal"]).tolist())

def test_macd_of_a_flat_series_is_zero():
    m = PriceAnalytics(series([50] * 40)).returnMACD()
    assert (m == 0).all().all()

def test_rate_of_change_is_percent_vs_period_rows_ago(pa):
    result = pa.returnRateOfChange(2)
    assert result.isna().tolist() == [True, True, False, False, False, False, False]
    assert result.dropna().tolist() == pytest.approx([5.0, (103 - 102) / 102 * 100, (101 - 105) / 105 * 100, (101 - 103) / 103 * 100, (104 - 101) / 101 * 100])
