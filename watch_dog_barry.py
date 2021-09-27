from watchdog.observers import Observer
from watchdog.events import *
import time
import sys


class FileEventHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    def on_moved(self, event):
        if event.is_directory:
            print("directory moved from {} to {}".format(event.src_path, event.dest_path))
        else:
            print("file moved from {} to {}".format(event.src_path, event.dest_path))
            self.task(filName=event.dest_path)

    def on_created(self, event):
        if event.is_directory:
            print("directory created:{}".format(event.src_path))
        else:
            print("file created:{}".format(event.src_path))

    def on_deleted(self, event):
        if event.is_directory:
            print("directory deleted:{}".format(event.src_path))
        else:
            print("file deleted:{}".format(event.src_path))

    def on_modified(self, event):
        if event.is_directory:
            print("directory modified:{}".format(event.src_path))
        else:
            print("file modified:{}".format(event.src_path))

    def task(self, filename):
        print(filename)
        # 具體任務


if __name__ == "__main__":
    observer = Observer()
    event_handler = FileEventHandler()
    filePath = sys.argv[1] if len(sys.argv) > 1 else '.'
    observer.schedule(event_handler, filePath, True)
    observer.start()

    time.sleep(100)

    observer.stop()
    observer.join()
