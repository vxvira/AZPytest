# private helpers

from ._log import warn

def _tradePnl(handling): # pnl of the open trade at the current price; entries hold signed contracts so long and short adds net out
    if handling.signedDirectionScale is None:
        return 0

    price   = handling.dataAtTick.price
    tickSz  = handling.config.tickSz
    tickVal = handling.config.tickVal

    return sum((price - entryPrice) / tickSz * tickVal * contracts for entryPrice, contracts in handling.entryData)

def _endTrade(handling): # realize the open trade's pnl and go flat
    handling._lastRealizedPnl      = _tradePnl(handling)
    handling.signedDirectionScale  = None
    handling.entryData             = [[None]]
    handling.entryIdx              = None

def _openTrade(handling, price, signed):
    handling.signedDirectionScale = signed
    handling.entryData            = [[price, signed]]
    handling.entryIdx             = handling.idx

def _addPosition(handling, contracts, sign):
    # adds change the net position: same side grows it, the opposite side shrinks it,
    # landing on zero ends the trade and crossing zero flips it into a new trade for the remainder
    price  = handling.dataAtTick.price
    signed = sign * contracts
    scale  = handling.signedDirectionScale

    if scale is None:
        _openTrade(handling, price, signed)
        return

    if signed * scale < 0:
        warn("adding to the opposite side of an open trade changes its shape: it shrinks the position, or flips it if it crosses zero")

    newScale = scale + signed
    if newScale * scale > 0: # still the same direction
        handling.signedDirectionScale = newScale
        handling.entryData.append([price, signed])
        return

    _endTrade(handling) # the offsetting part of this add is at the current price, so it adds no pnl of its own
    if newScale != 0: _openTrade(handling, price, newScale)

def _closePosition(handling, sign):
    if handling.signedDirectionScale is None:
        return
    if sign > 0 and handling.signedDirectionScale <= 0:
        return
    if sign < 0 and handling.signedDirectionScale >= 0:
        return

    _endTrade(handling)
