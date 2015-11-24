#!/usr/bin/env python
# coding:utf-8
import json

import sys
from server.monitor import start_monitor, set_mysql_config, list_charts, set_charts, stop_monitor
from server.my_util import patch_json, get_time
from server.web_socket import start_ws, clients


fp_log = open(sys.path[0] + "/result.txt", 'w')

# recv
r1 = '{"api":"set_cfg","content":["127.0.0.1",3306,"user","pass","docu","utf8"]}'
r2 = '{"api":"start_monitor"}'
r3 = '{"api":"list_charts"}'
r4 = '{"api":"set_charts","content":[]}'
r5 = '{"api":"stop_monitor"}'
# send
s0 = '{"api":"on_api","content":str}'
s1 = '{"api":"on_change","content":{}}'
s2 = '{"api":"list_charts","content":[]}'
s3 = '{"api":"on_stop"}'


def recv_data(content):
    print_data(content)
    try:
        api = json.loads(content)
        if api["api"] == 'set_cfg':
            cfg = api["content"]
            set_mysql_config(cfg[0], cfg[1], cfg[2], cfg[3], cfg[4], cfg[5])
        if api["api"] == 'start_monitor':
            start_monitor(on_db_changed, on_stop)
        if api["api"] == 'list_charts':
            list_charts(on_get_charts)
        if api["api"] == 'set_charts':
            set_charts(api["content"])
        if api["api"] == 'stop_monitor':
            stop_monitor()
    except Exception, ex:
        print Exception, ":", ex


def print_data(data):
    api = json.dumps({"api": "on_api", "content": data})
    send_data(api)
    print data


def on_get_charts(data):
    charts = {"api": "list_charts", "content": []}
    for t in data:
        for i in t:
            charts["content"].append(i)
    send_data(json.dumps(charts))


def send_data(data):
    for client in clients:
        client.send_data(data)


reload(sys)
sys.setdefaultencoding('utf-8')


def on_db_changed(result_str, result_dict):
    print result_str
    send_data(json.dumps({"api": "on_change", "content": result_dict}))
    try:
        fp_log.write("\n" + get_time() + result_str)
        fp_log.flush()
    except Exception, ex:
        print Exception, ":", ex


def on_stop():
    send_data(json.dumps({"api": "on_stop"}))


if __name__ == '__main__':
    patch_json()
    start_ws(recv_data)
