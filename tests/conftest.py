import logging

import pytest

import AZPytest.handling as h
from AZPytest._tooling import _log

CSV_HEADER = "price,ts_event,ts_recv,action\n"

@pytest.fixture(autouse=True)
def logs():
    """Records everything the azpytest logger emits; also resets warn()'s once-only memory between tests."""
    records = []

    class _Collect(logging.Handler):
        def emit(self, record): records.append(record)

    handler = _Collect()
    _log.logger.addHandler(handler)
    _log._warned.clear()
    yield records
    _log.logger.removeHandler(handler)
    _log._warned.clear()

@pytest.fixture
def make_handling(tmp_path):
    """make_handling([100, 102, ...]) -> Handling reading those prices (tickSz=1, tickVal=2), one row per price."""
    def make(prices, readFrom=1):
        path = tmp_path / "data.csv"
        rows = "".join(f"{p},{i + 1},{i + 1},T\n" for i, p in enumerate(prices))
        path.write_text(CSV_HEADER + rows)

        cfg = h.Configuration()
        cfg.path         = str(path)
        cfg.readFrom     = readFrom
        cfg.tickSz       = 1
        cfg.tickVal      = 2
        cfg.priceAlias   = "price"
        cfg.tsEventAlias = "ts_event"
        cfg.tsRecvAlias  = "ts_recv"
        cfg.actionAlias  = "action"
        cfg.buildConfig()
        return h.Handling(cfg)
    return make
