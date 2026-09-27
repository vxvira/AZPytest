import logging

import numpy as np
import pandas as pd
import pytest

from src.analytics.PriceAnalytics import PriceAnalytics
from src.analytics.SetAnalytics import SetAnalytics

def series(values, index=None): return pd.Series(values, index=index, dtype=float)

def test_manipulate_series_swaps_the_series():
    sa = SetAnalytics(series([1, 2, 3]))
    sa.ManipulateSeries(series([9]))
    assert sa.Series.tolist() == [9]

def test_rolling_moving_average():
    result = SetAnalytics(series([1, 2, 3, 4, 5])).returnRollingMovingAverage(3)
    assert result.isna().tolist() == [True, True, False, False, False]
    assert result.dropna().tolist() == [2, 3, 4]

def test_rolling_moving_average_matches_the_simple_moving_average():
    s = series(np.random.default_rng(1).normal(0, 1, 50))
    pd.testing.assert_series_equal(SetAnalytics(s).returnRollingMovingAverage(7), PriceAnalytics(s).returnSimpleMovingAveraage(7))

def test_zscore_over_the_whole_series():
    z = SetAnalytics(series([1, 2, 3, 4, 5])).returnZScore()
    r2 = 2 ** 0.5  # population std of 1..5
    assert z.tolist() == pytest.approx([-2 / r2, -1 / r2, 0, 1 / r2, 2 / r2])

def test_zscore_over_the_whole_series_has_mean_0_and_std_1():
    z = SetAnalytics(series(np.random.default_rng(2).normal(10, 3, 500))).returnZScore()
    assert z.mean() == pytest.approx(0, abs=1e-9)
    assert z.std(ddof=0) == pytest.approx(1)

def test_rolling_zscore_only_uses_the_window():
    z = SetAnalytics(series([1, 2, 3, 4, 100])).returnZScore(period=3)
    assert z.isna().tolist() == [True, True, False, False, False]
    assert z.iloc[2] == pytest.approx((3 - 2) / np.std([1, 2, 3]))
    assert z.iloc[4] == pytest.approx((100 - np.mean([3, 4, 100])) / np.std([3, 4, 100]))

def test_zscore_of_a_constant_series_is_nan():
    assert SetAnalytics(series([4, 4, 4])).returnZScore().isna().all()

def test_correlation_of_perfectly_related_series():
    a = SetAnalytics(series([1, 2, 3, 4]))
    assert a.returnPearsonCorrelation(series([2, 4, 6, 8])) == pytest.approx(1)
    assert a.returnPearsonCorrelation(series([8, 6, 4, 2])) == pytest.approx(-1)

def test_correlation_matches_numpy():
    rng = np.random.default_rng(3)
    x, y = rng.normal(0, 1, 100), rng.normal(0, 1, 100)
    assert SetAnalytics(series(x)).returnPearsonCorrelation(series(y)) == pytest.approx(np.corrcoef(x, y)[0, 1])

def test_rolling_correlation():
    a = SetAnalytics(series([1, 2, 3, 4, 3]))
    result = a.returnPearsonCorrelation(series([2, 4, 6, 8, 6]), period=3)
    assert result.isna().tolist() == [True, True, False, False, False]
    assert result.dropna().tolist() == pytest.approx([1, 1, 1])

def test_rolling_correlation_uses_only_the_window():
    rng = np.random.default_rng(4)
    x, y = rng.normal(0, 1, 60), rng.normal(0, 1, 60)
    result = SetAnalytics(series(x)).returnPearsonCorrelation(series(y), period=20)
    assert result.iloc[-1] == pytest.approx(np.corrcoef(x[-20:], y[-20:])[0, 1])

def test_tanh_values_and_bounds():
    result = SetAnalytics(series([-100, -1, 0, 1, 100])).returnTanh()
    assert result.tolist() == pytest.approx([-1, np.tanh(-1), 0, np.tanh(1), 1])
    assert result.between(-1, 1).all()

def test_tanh_preserves_the_index():
    s = series([0, 1], index=[10, 20])
    assert SetAnalytics(s).returnTanh().index.tolist() == [10, 20]

def test_fisher_transform_of_known_values():
    result = SetAnalytics(series([-0.5, 0, 0.5])).returnFisherTransform()
    assert result.tolist() == pytest.approx([-0.5 * np.log(3), 0, 0.5 * np.log(3)])

def test_fisher_transform_inverts_tanh():
    s = series(np.random.default_rng(5).normal(0, 1, 50))
    assert SetAnalytics(SetAnalytics(s).returnTanh()).returnFisherTransform().tolist() == pytest.approx(s.tolist())

@pytest.mark.parametrize("bad", [[0.2, 1.0], [-1.0, 0], [0, 3.5]])
def test_fisher_transform_without_a_period_is_fatal_outside_open_range(bad):
    with pytest.raises(ValueError, match=r"^\[fatal\] Fisher transform needs values strictly between -1 and 1"):
        SetAnalytics(series(bad)).returnFisherTransform()

def test_fisher_transform_with_a_period_rescales_to_the_window_first():
    result = SetAnalytics(series([1, 3, 2, 3, 1])).returnFisherTransform(period=3)
    assert result.isna().tolist() == [True, True, False, False, False]
    assert result.iloc[2] == pytest.approx(0)                       # 2 is midway between 1 and 3
    assert result.iloc[3] == pytest.approx(np.arctanh(0.999))       # 3 is the window high, clipped just inside 1
    assert result.iloc[4] == pytest.approx(np.arctanh(-0.999))      # 1 is the window low

def test_fisher_transform_with_a_period_is_nan_for_a_flat_window():
    assert SetAnalytics(series([5, 5, 5, 5])).returnFisherTransform(period=3).isna().all()

def test_fisher_transform_preserves_the_index():
    s = series([0.1, 0.2], index=[7, 8])
    assert SetAnalytics(s).returnFisherTransform().index.tolist() == [7, 8]

def test_spread_is_other_minus_self_entry_by_entry():
    result = SetAnalytics(series([1, 2, 3])).returnSpreadBetweenSeries(series([2, 4, 6]))
    assert result.tolist() == [1, 2, 3]

def test_spread_keeps_the_index_of_self_and_matches_by_position():
    s = series([1, 2, 3], index=[10, 20, 30])
    result = SetAnalytics(s).returnSpreadBetweenSeries(series([5, 5, 5], index=[7, 8, 9]))
    assert result.index.tolist() == [10, 20, 30]
    assert result.tolist() == [4, 3, 2]

def test_spread_accepts_a_plain_list():
    assert SetAnalytics(series([1, 2])).returnSpreadBetweenSeries([3, 3]).tolist() == [2, 1]

def test_spread_of_equal_lengths_does_not_warn(logs):
    SetAnalytics(series([1, 2, 3])).returnSpreadBetweenSeries(series([1, 2, 3]))
    assert logs == []

def test_spread_warns_and_trims_when_other_is_longer(logs):
    result = SetAnalytics(series([1, 2, 3])).returnSpreadBetweenSeries(series([10, 20, 30, 40, 50]))
    assert result.tolist() == [9, 18, 27]                            # the first 3 of other
    assert [(r.levelno, r.getMessage()) for r in logs] == [
        (logging.WARNING, "other has 5 entries, trimmed to the first 3 to match Series"),
    ]

def test_spread_warns_and_trims_series_when_other_is_shorter(logs):
    s = series([1, 2, 3, 4], index=[10, 20, 30, 40])
    result = SetAnalytics(s).returnSpreadBetweenSeries(series([5, 5]))
    assert result.tolist() == [4, 3]                                 # the first 2 of Series
    assert result.index.tolist() == [10, 20]
    assert [(r.levelno, r.getMessage()) for r in logs] == [
        (logging.WARNING, "Series has 4 entries, trimmed to the first 2 to match other"),
    ]
    assert s.tolist() == [1, 2, 3, 4]                                # the stored Series itself is untouched
