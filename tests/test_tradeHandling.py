import logging

# tickSz=1, tickVal=2 (see conftest), so pnl = price move * 2 * contracts

def test_addLong_opens_a_trade(make_handling):
    x = make_handling([100, 102])
    x.tick(); x.tick()
    x.addLong(3)
    assert x.signedDirectionScale == 3
    assert x.entryData == [[102, 3]]
    assert x.entryIdx == 2

def test_addShort_opens_a_negative_trade(make_handling):
    x = make_handling([100])
    x.tick()
    x.addShort(2)
    assert x.signedDirectionScale == -2
    assert x.entryData == [[100, -2]]

def test_scaling_in_accumulates_contracts_and_keeps_the_first_entry_idx(make_handling):
    x = make_handling([100, 102, 105])
    x.tick(); x.addLong(1)
    x.tick(); x.addLong(2)
    assert x.signedDirectionScale == 3
    assert x.entryData == [[100, 1], [102, 2]]
    assert x.entryIdx == 1

def test_closeLong_realizes_pnl_and_goes_flat(make_handling):
    x = make_handling([100, 105])
    x.tick(); x.addLong(2)
    x.tick(); x.closeLong()
    assert x.realizedPnl() == 5 * 2 * 2
    assert x.signedDirectionScale is None
    assert x.entryIdx is None
    assert x.unrealizedPnl() == 0

def test_closeShort_realizes_pnl(make_handling):
    x = make_handling([100, 96])
    x.tick(); x.addShort(1)
    x.tick(); x.closeShort()
    assert x.realizedPnl() == 4 * 2

def test_losing_trade_realizes_negative_pnl(make_handling):
    x = make_handling([100, 97])
    x.tick(); x.addLong(1)
    x.tick(); x.closeLong()
    assert x.realizedPnl() == -6

def test_closing_a_scaled_position_sums_every_entry(make_handling):
    x = make_handling([100, 102, 105])
    x.tick(); x.addLong(1)            # +5 ticks by the end
    x.tick(); x.addLong(2)            # +3 ticks * 2 contracts
    x.tick(); x.closeLong()
    assert x.realizedPnl() == (5 * 1 + 3 * 2) * 2

def test_close_is_a_noop_when_flat(make_handling):
    x = make_handling([100])
    x.tick()
    x.closeLong(); x.closeShort()
    assert x.realizedPnl() == 0
    assert x.signedDirectionScale is None

def test_closeShort_does_not_close_a_long_and_vice_versa(make_handling):
    x = make_handling([100, 105])
    x.tick(); x.addLong(1)
    x.tick(); x.closeShort()
    assert x.signedDirectionScale == 1
    assert x.realizedPnl() == 0

    y = make_handling([100, 105])
    y.tick(); y.addShort(1)
    y.tick(); y.closeLong()
    assert y.signedDirectionScale == -1
    assert y.realizedPnl() == 0

def test_realizedPnl_is_the_most_recent_trade_not_a_running_total(make_handling):
    x = make_handling([100, 105, 105, 103])
    x.tick(); x.addLong(1)
    x.tick(); x.closeLong()           # +10
    assert x.realizedPnl() == 10
    x.tick(); x.addLong(1)
    x.tick(); x.closeLong()           # -4
    assert x.realizedPnl() == -4

def test_realizedPnl_starts_at_zero(make_handling):
    assert make_handling([100]).realizedPnl() == 0

def test_unrealizedPnl_is_zero_when_flat(make_handling):
    x = make_handling([100])
    x.tick()
    assert x.unrealizedPnl() == 0

def test_unrealizedPnl_long_and_short_follow_the_price(make_handling):
    x = make_handling([100, 103, 98])
    x.tick(); x.addLong(1)
    x.tick(); assert x.unrealizedPnl() == 6
    x.tick(); assert x.unrealizedPnl() == -4

    y = make_handling([100, 103, 98])
    y.tick(); y.addShort(1)
    y.tick(); assert y.unrealizedPnl() == -6
    y.tick(); assert y.unrealizedPnl() == 4

def test_unrealizedPnl_covers_the_whole_open_trade(make_handling):
    x = make_handling([100, 102, 105])
    x.tick(); x.addLong(1)
    x.tick(); x.addLong(2)
    x.tick()
    assert x.unrealizedPnl() == (5 * 1 + 3 * 2) * 2

def test_positionsData_gets_a_row_per_tick_not_per_order(make_handling):
    x = make_handling([100, 101])
    x.tick(); x.addLong(1)
    assert len(x.positionsData) == 1
    x.tick()
    assert len(x.positionsData) == 2

SHAPE_WARNING = "adding to the opposite side of an open trade changes its shape: it shrinks the position, or flips it if it crosses zero"

def test_adding_the_opposite_side_shrinks_the_position(make_handling):
    x = make_handling([100, 102])
    x.tick(); x.addLong(3)
    x.tick(); x.addShort(1)
    assert x.signedDirectionScale == 2
    assert x.entryData == [[100, 3], [102, -1]]
    assert x.entryIdx == 1

def test_opposite_adds_warn_only_once(make_handling, logs):
    x = make_handling([100, 100, 100, 100])
    x.tick(); x.addLong(5)
    x.tick(); x.addShort(1)
    x.tick(); x.addShort(1)
    x.tick(); x.addShort(1)
    assert [(r.levelno, r.getMessage()) for r in logs] == [(logging.WARNING, SHAPE_WARNING)]

def test_adding_the_same_side_does_not_warn(make_handling, logs):
    x = make_handling([100, 101])
    x.tick(); x.addLong(1)
    x.tick(); x.addLong(1)
    assert logs == []

def test_unrealizedPnl_of_a_reduced_position_nets_the_reducing_entry(make_handling):
    x = make_handling([100, 102, 105])
    x.tick(); x.addLong(3)
    x.tick(); x.addShort(1)
    x.tick()
    assert x.unrealizedPnl() == 3 * 5 * 2 - 1 * 3 * 2

def test_closing_a_reduced_position_realizes_the_netted_pnl(make_handling):
    x = make_handling([100, 102, 105])
    x.tick(); x.addLong(3)
    x.tick(); x.addShort(1)
    x.tick(); x.closeLong()
    assert x.realizedPnl() == 3 * 5 * 2 - 1 * 3 * 2
    assert x.signedDirectionScale is None

def test_reducing_a_long_to_zero_ends_the_trade(make_handling):
    x = make_handling([100, 103, 103])
    x.tick(); x.addLong(2)
    x.tick(); x.addShort(2)
    assert x.signedDirectionScale is None
    assert x.entryData == [[None]]
    assert x.entryIdx is None
    assert x.realizedPnl() == 3 * 2 * 2
    assert x.unrealizedPnl() == 0
    x.tick()
    assert x.positionsData[-1] == [False, 0, None]

def test_reducing_a_short_to_zero_ends_the_trade(make_handling):
    x = make_handling([100, 103])
    x.tick(); x.addShort(1)
    x.tick(); x.addLong(1)
    assert x.signedDirectionScale is None
    assert x.realizedPnl() == -3 * 2

def test_a_new_trade_can_open_after_reducing_to_zero(make_handling):
    x = make_handling([100, 101, 102])
    x.tick(); x.addLong(1)
    x.tick(); x.addShort(1)
    x.tick(); x.addShort(2)
    assert x.signedDirectionScale == -2
    assert x.entryData == [[102, -2]]
    assert x.entryIdx == 3

def test_adding_past_zero_flips_a_long_into_a_short(make_handling):
    x = make_handling([100, 103])
    x.tick(); x.addLong(1)
    x.tick(); x.addShort(3)
    assert x.realizedPnl() == 3 * 2                 # the long closed at 103
    assert x.signedDirectionScale == -2
    assert x.entryData == [[103, -2]]               # only the remainder is the new trade
    assert x.entryIdx == 2
    assert x.unrealizedPnl() == 0

def test_adding_past_zero_flips_a_short_into_a_long(make_handling):
    x = make_handling([100, 96])
    x.tick(); x.addShort(2)
    x.tick(); x.addLong(5)
    assert x.realizedPnl() == 4 * 2 * 2
    assert x.signedDirectionScale == 3
    assert x.entryData == [[96, 3]]
    assert x.entryIdx == 2

def test_a_flipped_trade_tracks_and_closes_on_its_own(make_handling):
    x = make_handling([100, 103, 101, 99])
    x.tick(); x.addLong(1)
    x.tick(); x.addShort(3)                         # long +6 realized, now short 2 from 103
    x.tick(); assert x.unrealizedPnl() == 2 * 2 * 2 # price fell 2 ticks in our favour
    x.tick(); x.closeShort()
    assert x.realizedPnl() == 4 * 2 * 2             # the flipped trade only, not the earlier long

def test_flipping_shows_up_in_positionsData(make_handling):
    x = make_handling([100, 103, 103])
    x.tick(); x.addLong(1)
    x.tick(); x.addShort(3)
    x.tick()
    assert x.positionsData[-1] == [True, 0.0, 2]

def test_flipping_warns_once_like_any_opposite_add(make_handling, logs):
    x = make_handling([100, 100, 100])
    x.tick(); x.addLong(1)
    x.tick(); x.addShort(3)
    x.tick(); x.addLong(5)
    assert [r.getMessage() for r in logs] == [SHAPE_WARNING]
