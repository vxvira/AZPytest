# private helpers

def _addPosition(handling, contracts, sign):
    price = handling.data.price

    if handling.signedDirectionScale is None:
        handling.signedDirectionScale = sign * contracts
        handling.entryData = [[price, contracts]]
    else:
        handling.signedDirectionScale += sign * contracts
        handling.entryData.append([price, contracts])

def _closePosition(handling, sign):
    if handling.signedDirectionScale is None:
        return
    if sign > 0 and handling.signedDirectionScale <= 0:
        return
    if sign < 0 and handling.signedDirectionScale >= 0:
        return

    exitPrice = handling.data.price
    tickSz    = handling.config.tickSz
    tickVal   = handling.config.tickVal

    pnl = 0
    for entry in handling.entryData:
        entryPrice, contracts = entry
        ticks = sign * (exitPrice - entryPrice) / tickSz
        pnl  += ticks * tickVal * contracts

    handling.signedDirectionScale  = None
    handling.entryData             = [[None]]
    handling._realizedPnlAccum    += pnl
