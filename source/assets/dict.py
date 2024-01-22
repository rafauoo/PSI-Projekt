import threading

class SynchronizedDict:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def set_value(self, key, value):
        with self._lock:
            self._data[key] = value

    def get_value(self, key):
        with self._lock:
            return self._data.get(key)

    def remove_key(self, key):
        with self._lock:
            try:
                del self._data[key]
            except KeyError:
                pass  # Key not present, no need to remove

    def get_all_items(self):
        with self._lock:
            return dict(self._data)

    def get_all_keys(self):
        with self._lock:
            return self._data.keys()