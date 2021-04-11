"""Utilities for working with dates and time."""

import numpy as np
import pandas as pd
import dateparser
from datetime import datetime, timezone, timedelta, tzinfo, time
import pytz
import copy

from vectorbt.utils import typing as tp

__pdoc__ = {}

DatetimeIndexes = (pd.DatetimeIndex, pd.TimedeltaIndex, pd.PeriodIndex)

TimezoneLike = tp.Union[None, str, int, float, timedelta, tzinfo]
"""Any object that can be coerced into a timezone."""

DatetimeLike = tp.Union[str, int, float, pd.Timestamp, np.datetime64, datetime]
"""Any object that can be coerced into a datetime."""


def to_timedelta(arg: tp.Any, **kwargs) -> tp.Any:
    """`pd.to_timedelta` that uses unit abbreviation with number."""
    if isinstance(arg, str) and not arg[0].isdigit():
        # Otherwise "ValueError: unit abbreviation w/o a number"
        arg = '1' + arg
    return pd.to_timedelta(arg, **kwargs)


def get_utc_tz() -> timezone:
    """Get UTC timezone."""
    return timezone.utc


def get_local_tz() -> timezone:
    """Get local timezone."""
    return timezone(datetime.now(timezone.utc).astimezone().utcoffset())


def convert_tzaware_time(t: time, tz_out: tp.Optional[tzinfo]) -> time:
    """Return as non-naive time.

    `datetime.time` should have `tzinfo` set."""
    return datetime.combine(datetime.today(), t).astimezone(tz_out).timetz()


def tzaware_to_naive_time(t: time, tz_out: tp.Optional[tzinfo]) -> time:
    """Return as naive time.

    `datetime.time` should have `tzinfo` set."""
    return datetime.combine(datetime.today(), t).astimezone(tz_out).time()


def naive_to_tzaware_time(t: time, tz_out: tp.Optional[tzinfo]) -> time:
    """Return as non-naive time.

    `datetime.time` should not have `tzinfo` set."""
    return datetime.combine(datetime.today(), t).astimezone(tz_out).time().replace(tzinfo=tz_out)


def convert_naive_time(t: time, tz_out: tp.Optional[tzinfo]) -> time:
    """Return as naive time.

    `datetime.time` should not have `tzinfo` set."""
    return datetime.combine(datetime.today(), t).astimezone(tz_out).time()


def is_tz_aware(dt: datetime) -> bool:
    """Whether datetime is timezone-aware."""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def to_timezone(tz: TimezoneLike, **kwargs) -> tzinfo:
    """Parse the timezone.

    Strings are parsed by `pytz` and `dateparser`, while integers and floats are treated as hour offsets.

    If the timezone object can't be checked for equality based on its properties,
    it's automatically converted to `datetime.timezone`.

    `**kwargs` are passed to `dateparser.parse`."""
    if tz is None:
        return get_local_tz()
    if isinstance(tz, str):
        try:
            tz = pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            dt = dateparser.parse('now %s' % tz, **kwargs)
            if dt is not None:
                tz = dt.tzinfo
    if isinstance(tz, (int, float)):
        tz = timezone(timedelta(hours=tz))
    if isinstance(tz, timedelta):
        tz = timezone(tz)
    if isinstance(tz, tzinfo):
        if tz != copy.copy(tz):
            return timezone(tz.utcoffset(datetime.now()))
        return tz
    raise TypeError("Couldn't parse the timezone")


def to_tzaware_datetime(dt: DatetimeLike, tz: tp.Optional[TimezoneLike] = None, **kwargs) -> datetime:
    """Parse the datetime as a timezone-aware `datetime.datetime`.

    See [dateparser docs](http://dateparser.readthedocs.io/en/latest/) for valid string formats and `**kwargs`.

    Timestamps are localized to UTC, while naive datetime is localized to the local time.
    To explicitly convert the datetime to a timezone, use `tz` (uses `to_timezone`)."""
    if isinstance(dt, float):
        dt = datetime.fromtimestamp(dt, timezone.utc)
    elif isinstance(dt, int):
        if len(str(dt)) > 10:
            dt = datetime.fromtimestamp(dt / 10 ** (len(str(dt)) - 10), timezone.utc)
        else:
            dt = datetime.fromtimestamp(dt, timezone.utc)
    elif isinstance(dt, str):
        dt = dateparser.parse(dt, **kwargs)
        if dt is None:
            raise ValueError("Couldn't parse the datetime")
    elif isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    elif isinstance(dt, np.datetime64):
        dt = dt.astype(datetime)

    if not is_tz_aware(dt):
        dt = dt.replace(tzinfo=get_local_tz())
    else:
        dt = dt.replace(tzinfo=to_timezone(dt.tzinfo))
    if tz is not None:
        dt = dt.astimezone(to_timezone(tz))
    return dt


def datetime_to_ms(dt: datetime) -> int:
    """Convert a datetime to milliseconds."""
    epoch = datetime.fromtimestamp(0, dt.tzinfo)
    return int((dt - epoch).total_seconds() * 1000.0)


def interval_to_ms(interval: str) -> tp.Optional[int]:
    """Convert an interval string to milliseconds."""
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60,
    }
    try:
        return int(interval[:-1]) * seconds_per_unit[interval[-1]] * 1000
    except (ValueError, KeyError):
        return None
