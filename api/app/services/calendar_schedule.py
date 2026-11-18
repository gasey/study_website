"""Shared projections of existing schedules; never create participation or awards."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from .games import cup_window


def community(start, end):
    local = ZoneInfo('Asia/Kolkata')
    cursor = datetime.combine(start, time.min, local)
    result = []
    while True:
        cid, opens, closes = cup_window(cursor)
        if opens.date() > end:
            break
        result.append({'id':'cup:'+cid, 'day':opens.date(), 'title':'Weekly Cup · 7–8 pm India time',
                       'starts_at':opens, 'ends_at':closes, 'url':'/games?mode=cup', 'kind':'cup'})
        cursor = closes + timedelta(seconds=1)
    return result
