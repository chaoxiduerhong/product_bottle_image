# -*- coding:utf-8 -*-
# Desc: 模拟在线gpt，切勿用于商业用途

from threading import Thread
from threading import Lock
from spider.Base import Base as GPTRobots
from config import browser_conf

thread_lock = Lock()

def async_call(fn):
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper


@async_call
def go_running(thread_name):
    # 检测是否带了
    rob = GPTRobots(thread_lock=thread_lock, thread_name=thread_name)
    rob.query()


# Jun 04 2024 - 启动线程时, thread 不再固定绑定一个 port
def run(mode):
    # 这里只是通过 browser 数量确定 thread 数量
    for idx in range(0,20):
        thread_name = str(idx)
        go_running(thread_name)


def start(mode):
    run(mode)