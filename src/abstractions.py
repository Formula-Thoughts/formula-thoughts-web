import typing
from dataclasses import field, dataclass
from typing import Protocol


@dataclass(unsafe_hash=True)
class Error:
    message: str = None


@dataclass(unsafe_hash=True)
class ApplicationContext:
    body: dict = None
    auth_user_id: str = None
    parameters: dict = None
    error_capsules: list[Error] = field(default_factory=lambda: [])
    response: typing.Any = None


class Command(Protocol):

    def run(self, context: ApplicationContext) -> None:
        ...


class RequestHandler(Protocol):

    def run(self, event: dict) -> ApplicationContext:
        ...

    @property
    def route_key(self) -> str:
        ...


class SequenceBuilder(Protocol):

    def generate_sequence(self) -> list[Command]:
        ...

    def build(self):
        ...


SequenceComponent = typing.Union[SequenceBuilder, Command]


class Serializer(Protocol):

    def serialize(self, data: typing.Union[dict, list]) -> str:
        ...


class Deserializer(Protocol):

    def deserialize(self, data: str) -> typing.Union[dict, list]:
        ...


LoggerType = typing.TypeVar('LoggerType')


class Logger(Protocol[LoggerType]):

    def add_global_properties(self, properties: dict):
        ...

    def log_error(self, message: str, properties: dict = None):
        ...

    def log_exception(self, exception: Exception, properties: dict = None):
        ...

    def log_info(self, message: str, properties: dict = None):
        ...

    def log_event(self, message: str, properties: dict = None):
        ...

    def log_debug(self, message: str, properties: dict = None):
        ...

    def log_trace(self, message: str, properties: dict = None):
        ...
