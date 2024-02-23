class DummyLogger:

    def add_global_properties(self, properties: dict):
        ...

    def log_error(self, message: str, properties: dict = None):
        ...

    def log_exception(self, exception: Exception, properties: dict = None):
        ...

    def log_event(self, message: str, properties: dict = None):
        ...

    def log_info(self, message: str, properties: dict = None):
        ...

    def log_debug(self, message: str, properties: dict = None):
        ...

    def log_trace(self, message: str, properties: dict = None):
        ...


def logger_factory():
    return DummyLogger()