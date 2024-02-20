class DummyLogger:

    def log_error(self, message: str):
        ...

    def log_exception(self, exception: Exception):
        ...

    def log_info(self, message: str):
        ...

    def log_debug(self, message: str):
        ...

    def log_trace(self, message: str):
        ...


def logger_factory():
    return DummyLogger()