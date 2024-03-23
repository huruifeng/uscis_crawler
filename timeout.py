# Timeout handle adapter
from requests.adapters import HTTPAdapter
class TimeoutHttpAdapter(HTTPAdapter):
    def __init__(self, timeout=None, *args, **kwargs):
        self.timeout = timeout
        if "timeout" in kwargs:
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, *args, **kwargs):
        kwargs['timeout'] = self.timeout
        return super().send(*args, **kwargs)