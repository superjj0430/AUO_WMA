import json
import time

import portalocker
from concurrent.futures import ThreadPoolExecutor
import queue


def demo(x):
    print(x)
    with open("index.json", "r") as index_file:
        index_data = json.load(index_file)
        index_data['file_name'].append(x)
        print(index_data['file_name'])

    with open("index.json", "w") as index_file:
        portalocker.lock(index_file, portalocker.LOCK_EX)
        index_file.write(json.dumps(index_data))
        portalocker.unlock(index_file)


def thread_pool_callback(worker):
    print('done', time.time())


if __name__ == "__main__":
    executor = ThreadPoolExecutor(max_workers=3)

    task1 = executor.submit(demo, "aaa")
    task1.add_done_callback(thread_pool_callback)
    # task2 = executor.submit(demo, "bbb")
    # task2.add_done_callback(thread_pool_callback)
    # task3 = executor.submit(demo, "ccc")
    # task3.add_done_callback(thread_pool_callback)
