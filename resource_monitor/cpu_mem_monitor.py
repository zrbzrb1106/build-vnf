#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Monitor CPU and Memory Usage, used for resource monitoring of different VNF implementations
Email: xianglinks@gmail.com

Problem: The program doesn't know when receiving starts and ends, so it's
         diffcult to perfrom event based measurement.
"""

import sched
import sys
import time

import psutil

GET_CPU_PERIOD_S = 0.01
LOG_CPU_PERIOD_S = 3
CPU_LOG_FILE = "./cpu_usage.csv"
CPU_USAGE = list()
VNF_PROC_NAME = "udp_append_ts"


def find_proc(proc_name):
    for p in psutil.process_iter():
        if p.name() == proc_name:
            print("[INFO] Find proc for %s, pid: %d" % (p.name(), p.ppid()))
            return p
    else:
        return None


def get_cpu_usage(scheduler, proc):
    CPU_USAGE.append(proc.cpu_percent())
    scheduler.enter(GET_CPU_PERIOD_S, 1, get_cpu_usage,
                    argument=(scheduler, proc))


def log_cpu_usage(scheduler):
    # Log CPU usage, SHOULD be fast
    with open(CPU_LOG_FILE, 'a+') as log_file:
        text = ','.join(map(str, CPU_USAGE)) + ','
        log_file.write(text)
    CPU_USAGE.clear()
    # Add the task in the queue
    scheduler.enter(LOG_CPU_PERIOD_S, 2, log_cpu_usage,
                    argument=(scheduler, ))


def main():
    # Wait until the VNF proc is running
    while True:
        vnf_p = find_proc(VNF_PROC_NAME)
        if vnf_p:
            break
        print("VNF proc: %s is not running, keep waiting..." % VNF_PROC_NAME)
        time.sleep(0.5)

    time.sleep(1)  # Wait for the init procs
    # Start monitoring CPU usage
    print("[INFO] Start monitoring CPU usage...")
    # MARK: Currently not so optimized for automatic tests
    with open(CPU_LOG_FILE, 'a+') as log_file:
        log_file.write('\n')
    scheduler = sched.scheduler(timefunc=time.time, delayfunc=time.sleep)
    scheduler.enter(GET_CPU_PERIOD_S, 1, get_cpu_usage,
                    argument=(scheduler, vnf_p))
    scheduler.enter(LOG_CPU_PERIOD_S, 2, log_cpu_usage,
                    argument=(scheduler, ))

    try:
        scheduler.run(blocking=True)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, exit the program...")
        sys.exit(0)


if __name__ == '__main__':
    main()