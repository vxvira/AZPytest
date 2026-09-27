import logging

import pytest

from src._tooling import _log

def test_warn_logs_at_warning_level(logs):
    _log.warn("something odd")
    assert [(r.levelno, r.getMessage()) for r in logs] == [(logging.WARNING, "something odd")]

def test_warn_reports_each_distinct_message_once(logs):
    _log.warn("same")
    _log.warn("same")
    _log.warn("different")
    assert [r.getMessage() for r in logs] == ["same", "different"]

def test_fatal_raises_value_error_with_prefix():
    with pytest.raises(ValueError, match=r"^\[fatal\] it broke$"):
        _log.fatal("it broke")

def test_fatal_does_not_log(logs):
    with pytest.raises(ValueError):
        _log.fatal("it broke")
    assert logs == []

def test_default_formatter_tags_levels():
    fmt = _log._TagFormatter("[%(tag)s] %(message)s")
    record = logging.LogRecord("azpytest", logging.WARNING, __file__, 1, "hello", None, None)
    assert fmt.format(record) == "[warn] hello"
    record.levelno = logging.CRITICAL
    assert fmt.format(record) == "[fatal] hello"
