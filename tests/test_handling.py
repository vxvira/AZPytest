import pytest

import AZPytest.handling as h

def config(**overrides):
    c = h.Configuration()
    c.path = "data.csv"
    for k, v in overrides.items(): setattr(c, k, v)
    return c

def test_buildConfig_collects_only_the_set_aliases():
    c = config(priceAlias="price", actionAlias="action")
    c.buildConfig()
    assert c.aliases == ["price", "action"]

def test_buildConfig_without_path_is_fatal():
    with pytest.raises(ValueError, match=r"^\[fatal\] path not set$"):
        h.Configuration().buildConfig()

def test_buildConfig_warns_for_each_unset_alias(logs):
    config(priceAlias="price").buildConfig()
    assert [r.getMessage() for r in logs] == ["tsEventAlias not set", "tsRecvAlias not set", "actionAlias not set"]

def test_buildConfig_with_everything_set_is_silent(logs):
    config(priceAlias="p", tsEventAlias="e", tsRecvAlias="r", actionAlias="a").buildConfig()
    assert logs == []

def test_data_updaters_set_their_field():
    d = h.Data()
    d.updatePrice(1.5); d.updateTsEvent(2); d.updateTsRecv(3); d.updateAction("T")
    assert (d.price, d.tsEvent, d.tsRecv, d.action) == (1.5, 2, 3, "T")

def test_dataseries_stores_a_snapshot_per_tick_not_the_same_object():
    d = h.Data()
    s = h.DataSeries(d)
    d.updatePrice(1); d.updateAction("A"); s.tick()
    d.updatePrice(2); d.updateAction("T"); s.tick()
    assert s.price == [1, 2]
    assert s.action == ["A", "T"]
    assert s.tsEvent == [0, 0]

def test_tick_reads_rows_in_order_and_advances_idx(make_handling):
    x = make_handling([100, 102, 105])
    assert x.idx == 0
    x.tick()
    assert (x.idx, x.dataAtTick.price, x.dataAtTick.tsEvent) == (1, 100, 1)
    x.tick()
    assert (x.idx, x.dataAtTick.price) == (2, 102)

def test_tick_appends_to_the_series(make_handling):
    x = make_handling([100, 102, 105])
    for _ in range(3): x.tick()
    assert x.data.price == [100, 102, 105]
    assert x.data.tsEvent == [1, 2, 3]
    assert x.data.action == ["T", "T", "T"]

def test_readFrom_skips_leading_rows_and_idx_matches_the_row_number(make_handling):
    x = make_handling([10, 20, 30, 40, 50], readFrom=3)
    x.tick()
    assert (x.idx, x.dataAtTick.price) == (3, 30)

def test_tick_past_the_end_raises_stopiteration(make_handling):
    x = make_handling([100])
    x.tick()
    with pytest.raises(StopIteration):
        x.tick()

def test_tick_with_unset_aliases_leaves_those_fields_at_default(tmp_path):
    (tmp_path / "d.csv").write_text("price,ts_event\n7,9\n")
    c = config(path=str(tmp_path / "d.csv"), priceAlias="price", tsEventAlias="ts_event")
    c.buildConfig()
    x = h.Handling(c)
    x.tick()
    assert (x.dataAtTick.price, x.dataAtTick.tsEvent, x.dataAtTick.tsRecv, x.dataAtTick.action) == (7, 9, 0, 0)

def test_tick_records_position_state_each_tick(make_handling):
    x = make_handling([100, 102, 105, 103, 101])
    x.tick(); x.tick()
    x.addLong(1)                      # entered at 102 on idx 2
    x.tick(); x.tick()                # prices 105, 103
    x.closeLong()
    x.tick()
    assert x.positionsData == [
        [False, 0,    None],
        [False, 0,    None],
        [True,  6.0,  2],             # (105 - 102) ticks * 2
        [True,  2.0,  2],             # (103 - 102) ticks * 2
        [False, 0,    None],
    ]

def test_api_methods_delegate(make_handling):
    x = make_handling([100, 104])
    x.tick(); x.addShort(2); x.tick()
    assert x.unrealizedPnl() == -16   # short 2, price up 4 ticks * 2 * 2
    x.closeShort()
    assert x.realizedPnl() == -16
    assert x.unrealizedPnl() == 0
