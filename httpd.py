#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from _socket import SOL_SOCKET, SO_REUSEADDR
import sys
import time

from utils import determinate_content_type, make_40X_resopnse_header, read_file, make_response_header, http_parser, \
    change_base_dir, get_base_dir, get_ncpu, decode_url
import threading

is_live = True


def check_data_for_thread(index):
    global thread_data_dict
    return thread_data_dict[index] if thread_data_dict[index] else False


def set_data_for_thread(index, data):
    global thread_data_dict
    thread_data_dict[index] = data


def get_is_live():
    global is_live
    return is_live


def worker(index, event):
    is_live = get_is_live()
    while is_live:
        is_live = get_is_live()
        print "thread-{} start".format(index)
        event.wait()
        _time = time.time()
        conn = check_data_for_thread(index)
        data = ""
        new_data = True
        while b"\r\n" not in data and new_data:
            new_data = conn.recv(1024)
            if new_data:
                data += new_data
            else:
                break
        print "----------CLEARDATA---------"
        print data
        data = decode_url(data)
        print "------DATA--------"
        print data
        method, path, http_version = http_parser(data)
        print "------------PARAMETERS----------"
        print method, path, http_version
        if not method or not path or not http_version:
            try:
                conn.send(make_40X_resopnse_header("405 Bad Gateway"))
            except BaseException as e:
                conn.close()
                set_data_for_thread(index, None)
                event.clear()
                continue
        else:
            is_data_type_determinate, data_type = determinate_content_type(path)
            try:
                if not is_data_type_determinate:
                    path += 'index.html'
                data, length = read_file(path)
            except IOError:
                conn.send(make_40X_resopnse_header("404 Not Found"))
                conn.close()
                set_data_for_thread(index, None)
                event.clear()
                continue
            try:
                header = make_response_header(data_type, length, http_version)

                if method == "GET":
                    data = header + data
                    conn.send(data)
                if method == "HEAD":
                    data = header
                    conn.send(data)
            except BaseException as e:
                print "404 BASE in thread-{}".format(index)
                print path
                print e
        try:
            conn.close()
        except Exception as e:
            print e
        set_data_for_thread(index, None)
        event.clear()
        print "thread-{} stop".format(index)

thread_data_dict = list()
thread_list = list()
events_list = list()

if __name__ == "__main__":
    _r_flag = False
    _c_flag = False
    for param in sys.argv:
        if _r_flag:
            print param
            change_base_dir(param)
            # проверить, что существует директория
            _r_flag = False
        if _c_flag:
            try:
                NCPU = int(param)
            except Exception as e:
                print "-c parameter should be int"
                raise Exception
            _c_flag = False
        if param == '-r':
            _r_flag = True
            continue
        if param == '-c':
            _c_flag = True
            continue

if not get_base_dir():
    raise Exception

print "BASE_DIR:", get_base_dir()
print "NCPU:", get_ncpu()
try:
    for thread_index in range(0, 10):
        _event = threading.Event()
        events_list.append(_event)
        thread_data_dict.append(False)
        thread_list.append(threading.Thread(target=worker, args=(thread_index, _event)))

    for thread in thread_list:
        thread.start()

    while True:
        try:
            print "server_start"
            sock = socket.socket()
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            sock.bind(('', 80))
            sock.listen(1)
            conn, addr = sock.accept()
            for i in range(0, thread_data_dict.__len__()):
                if not thread_data_dict[i]:
                    set_data_for_thread(i,conn)
                    events_list[i].set()
                    break
        except BaseException as e:
            print 'BaseException'
            print e

    is_live = False

    for thread in thread_list:
        thread.join()
except Exception as e:
    print e