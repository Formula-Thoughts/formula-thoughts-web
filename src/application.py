import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, Union

from src.abstractions import Logger

SUBSEQUENCE = "subsequence"
COMMAND = "command"


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
    body: dict = None
    error_capsules: list[Error] = field(default_factory=lambda: [])
    response: Response = None


class Command(Protocol):

    def run(self, context: ApplicationContext) -> None:
        ...


class SequenceBuilder(Protocol):

    def generate_sequence(self) -> list[Command]:
        ...

    def build(self):
        ...


SequenceComponent = Union[SequenceBuilder, Command]


class FluentSequenceBuilder(ABC):

    def __init__(self):
        self.__components: list[(str, SequenceComponent)] = []

    def _add_command(self, command: Command) -> 'FluentSequenceBuilder':
        self.__components.append((COMMAND, command))
        return self

    def _add_sequence_builder(self, sequence_builder: SequenceBuilder) -> 'FluentSequenceBuilder':
        self.__components.append((SUBSEQUENCE, sequence_builder))
        return self

    def generate_sequence(self) -> list[Command]:
        self.build()
        new_list = []
        for (name, component) in self.__components:
            if name == COMMAND:
                new_list.append(component)
            if name == SUBSEQUENCE:
                sequence_component: SequenceBuilder = component
                commands = sequence_component.generate_sequence()
                new_list.extend(commands)
        return new_list

    @abstractmethod
    def build(self):
        ...

    @property
    def components(self) -> list[SequenceComponent]:
        return list(map(lambda x: x[1], self.__components))


class MiddlewarePipeline:

    def __init__(self, logger: Logger):
        self.__logger = logger

    def execute_middleware(self, context: ApplicationContext,
                           sequence: SequenceBuilder):
        middleware = sequence.generate_sequence()
        for action in middleware:
            name = "anonymous"
            try:
                name = f"{inspect.getmodule(action).__name__}.{action.__name__}"
            except Exception:
                ...
            self.__logger.log_debug(f"begin middleware {name}")
            self.__logger.log_trace(f"request {context.body}")
            self.__logger.log_trace(f"response {context.response.body}")
            action.run(context)
            # for now, we throw on first error in top level sequence
            if any(context.error_capsules):
                error = context.error_capsules[-1]
                self.__logger.log_error(f"error found in error capsule {type(error).__name__}")
                context.response.body = {"message": error.msg}
                context.response.status_code = error.status_code
                self.__logger.log_error(f"middleware SHORTED!")
                break
            self.__logger.log_debug(f"end middleware {name}")