#!/usr/bin/env python
# coding:utf-8
import json
import time
import datetime


def get_time(f='%m-%d %H:%M:%S'):
    return time.strftime(f, time.localtime(time.time()))


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        else:
            return super(_JSONEncoder, self).default(o)


def patch_json():
    def dumps(obj, *args, **kwargs):
        return _JSONEncoder(*args, **kwargs).encode(obj)

    json.dumps = dumps
