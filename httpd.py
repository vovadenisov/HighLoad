#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from _socket import SOL_SOCKET, SO_REUSEADDR
import sys
import time

from multiprocessing import freeze_support, Process

from utils import determinate_content_type, make_40X_resopnse_header, read_file, make_response_header, http_parser, \
    get_ncpu, decode_url, set_ncpu
import threading


def check_data_for_thread(index):
    global thread_data_dict
    return thread_data_dict[index] if thread_data_dict[index] else False


def set_data_for_thread(index, data):
    global thread_data_dict
    thread_data_dict[index] = data


def worker(index, event, base_url):
    while True:
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
        data = decode_url(data)
        method, path, http_version = http_parser(data)
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
                data, length = read_file(path, base_url)
            except IOError:
                if is_data_type_determinate:
                    conn.send(make_40X_resopnse_header("404 Not Found"))
                else:
                    conn.send(make_40X_resopnse_header("403 Forbidden"))
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
base_dir = None

if __name__ == "__main__":
    _r_flag = False
    _c_flag = False
    for param in sys.argv:
        if _r_flag:
            print param
            base_dir = param
            # проверить, что существует директория
            _r_flag = False
        if _c_flag:
            try:
                set_ncpu(int(param))
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

if not base_dir:
    raise Exception

print "BASE_DIR:", base_dir
print "NCPU:", get_ncpu()


def process(base_url, process_index, sock):
    print "process_start-{}".format(process_index)
    try:
        for thread_index in range(0, 10):
            _event = threading.Event()
            events_list.append(_event)
            thread_data_dict.append(False)
            thread_list.append(threading.Thread(target=worker, args=(thread_index, _event, base_url)))

        for thread in thread_list:
            thread.start()
        print "thread_start in process-{}".format(process_index)
        while True:
            try:
                print "server_start"
                conn, addr = sock.accept()
                print "socket_accept in process-{}".format(process_index)
                for i in range(0, thread_data_dict.__len__()):
                    if not thread_data_dict[i]:
                        set_data_for_thread(i,conn)
                        events_list[i].set()
                        break
            except BaseException as e:
                print 'BaseException'
                print e

        for thread in thread_list:
            thread.join()
    except Exception as e:
        print e

if __name__ == "__main__":
    freeze_support()
    process_list = []
    sock = socket.socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(('', 80))
    sock.listen(1)
    for index in range(0, get_ncpu()):
        process_list.append(Process(target=process, args=(base_dir, index, sock)))
    for index in range(0, get_ncpu()):
        process_list[index].start()
    for index in range(0, get_ncpu()):
        process_list[index].join()