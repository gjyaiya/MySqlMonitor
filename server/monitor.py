import copy
import threading
import time
import MySQLdb
from my_util import get_time

HOST = ''
PORT = 0
USERNAME = ''
PASSWORD = ''
DATABASE = ''
CHARSET = ''

MONITOR_TIME = 10
RETRY_TIME = 5
STOP = False
monitor_charts = ["chars", "map", "rules", "thesis", "patent"]


def set_mysql_config(host, port, username, password, database, charset):
    global HOST, PORT, USERNAME, PASSWORD, DATABASE, CHARSET
    HOST = host
    PORT = port
    USERNAME = username
    PASSWORD = password
    DATABASE = database
    CHARSET = charset


def start_monitor(on_db_changed, on_stop):
    t = threading.Thread(target=mysql_monitor_auto, args=[on_db_changed, on_stop])
    t.start()


def set_charts(charts):
    global monitor_charts
    monitor_charts = charts


def list_charts(on_get_charts):
    global cur, conn
    try:
        conn = MySQLdb.connect(host=HOST, user=USERNAME, passwd=PASSWORD, db=DATABASE, port=PORT, charset=CHARSET)
        cur = conn.cursor()
        cur.execute('show tables;')
        rs = cur.fetchall()
        on_get_charts(rs)
    except MySQLdb.Error, e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
    finally:
        cur.close()
        conn.close()


def format_result(chart_name, pre_set, current_set):
    return chart_name + " : Record changed\n" + \
           ("Old:" + str(list(pre_set - current_set)) + "\nNew:" + str(list(current_set - pre_set))).decode(
               "unicode-escape") + "\n"


def get_records(cursor):
    result = {}
    for i in monitor_charts:
        cursor.execute('select * from ' + i)
        rs = cursor.fetchall()[:]
        head = map(lambda x: x[0], cursor.description)
        result[i] = {'rs': rs, 'head': head}
    return result


def get_result(chart, head, pre, last):
    result = {"result": 0, "time": get_time(), "chart": chart, "head": head, "old": [], "new": []}
    pset, lset = set(pre), set(last)
    if len(pset) != len(pre) or len(lset) != len(last):
        result["result"] = 2
        result["comment"] = "Length don't same ,please niu check"
        return result
    old, new = list(pset - lset), list(lset - pset)
    if len(old) == 0 and len(new) == 0:
        result["comment"] = "No Record Change"
        return result
    result["result"], result["old"], result["new"] = 1, old, new
    if len(old) == 0:
        result["comment"] = "Add " + str(len(new)) + " Records"
    elif len(new) == 0:
        result["comment"] = "Delete " + str(len(old)) + " Records"
    else:
        result["comment"] = "Old: " + str(len(old)) + "   New: " + str(len(new)) + " "
    return result


def mysql_monitor_auto(on_db_changed, on_stop):
    global RETRY_TIME, STOP
    STOP = False
    while RETRY_TIME > 0 and not STOP:
        mysql_monitor(on_db_changed)
        RETRY_TIME -= 1
    on_stop()
    print "Monitor stop"


def stop_monitor():
    global STOP
    STOP = True


def mysql_monitor(on_db_changed):
    global cur, conn
    global HOST, PORT, USERNAME, PASSWORD, DATABASE, CHARSET, RETRY_TIME
    try:
        conn = MySQLdb.connect(host=HOST, user=USERNAME, passwd=PASSWORD, db=DATABASE, port=PORT, charset=CHARSET)
        RETRY_TIME = 5
        cur = conn.cursor()
        pre = get_records(cur)
        while not STOP:
            changed = False
            time.sleep(MONITOR_TIME)
            conn.commit()
            last = get_records(cur)

            for i in monitor_charts:
                result = get_result(i, last[i]['head'], pre[i]['rs'], last[i]['rs'])
                if result['result'] == 2:
                    print i + ": Length don't same ,please niu check~\n"
                if result['result'] == 1:
                    changed = True
                    on_db_changed(format_result(i, set(pre[i]['rs']), set(last[i]['rs'])), result)
            if not changed:
                print get_time() + ' No change'
            else:
                pre = copy.deepcopy(last)
    except MySQLdb.Error, e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
    except Exception, e:
        print "Exception %d: %s" % (e.args[0], e.args[1])
    finally:
        cur.close()
        conn.close()
        return True
