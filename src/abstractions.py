import typing
from dataclasses import field, dataclass
from typing import Protocol


@dataclass(unsafe_hash=True)
class Response:
    body: dict = None
    status_code: int = None


@dataclass(unsafe_hash=True)
class Error:
    msg: str = None
    status_code: int = None


@dataclass(unsafe_hash=True)
class ApplicationContext:
    body: typing.Union[dict, str, list] = None
    auth_user_id: str = None
    parameters: dict = None
    error_capsules: list[Error] = field(default_factory=lambda: [])
    response: Response = None


class Command(Protocol):

    def run(self, context: ApplicationContext) -> None:
        ...


class RequestHandler(Protocol):

    def run(self, event: dict) -> None:
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


class Logger(Protocol):

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
