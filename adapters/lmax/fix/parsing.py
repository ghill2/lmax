import pandas as pd

from nautilus_trader.core.datetime import dt_to_unix_nanos


def parse_lmax_timestamp_ns(value: str) -> int:
    return dt_to_unix_nanos(pd.to_datetime(value, format="%Y%m%d-%H:%M:%S.%f"))  # TransactTime


def format_lmax_timestamp(value: pd.Timestamp) -> str:
    """
    Representing Time/date combination represented in UTC (Universal Time Coordinated, also known as GMT )
    only accepted in this format : YYYYMMDD-HH:MM:SS (whole seconds).
    For example 20120321-17:15:03
    """
    return value.strftime("%Y%m%d-%H:%M:%S")


def parse_lmax_reject_reason(value: int) -> str:
    """
    Tag 103 Code to identify reason for order rejection.

    Note: Values 3, 4, and 5 will be used when rejecting an order due to pre-allocation information errors.

    """
    if value == 0:
        return "Broker / Exchange option"
    elif value == 1:
        return "Unknown symbol"
    elif value == 2:
        return "Exchange closed"
    elif value == 3:
        return "Order exceeds limit"
    elif value == 4:
        return "Too late to enter"
    elif value == 5:
        return "Unknown Order"
    elif value == 6:
        return "Duplicate Order (e.g. duplicate ClOrdID ())"
    elif value == 7:
        return "Duplicate of a verbally communicated order"
    elif value == 8:
        return "Stale Order"
    elif value == 9:
        return "Trade Along required"
    elif value == 10:
        return "Invalid Investor ID"
    elif value == 11:
        return "Unsupported order characteristic"
    elif value == 12:
        return "Surveillence Option"
    elif value == 13:
        return "Incorrect quantity"
    elif value == 14:
        return "Incorrect allocated quantity"
    elif value == 15:
        return "Unknown account(s)"
    elif value == 99:
        return "Other"
