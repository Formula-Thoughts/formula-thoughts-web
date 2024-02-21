import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, Union

from src.abstractions import Logger, SequenceComponent, Command, SequenceBuilder, ApplicationContext, ErrorResponse

SUBSEQUENCE = "subsequence"
COMMAND = "command"


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


class TopLevelSequenceRunner:

    def __init__(self, logger: Logger):
        self.__logger = logger

    def run(self, context: ApplicationContext,
            top_level_sequence: SequenceBuilder):
        middleware = top_level_sequence.generate_sequence()
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
                context.response = ErrorResponse(body=error)
                self.__logger.log_error(f"middleware SHORTED!")
                break
            self.__logger.log_debug(f"end middleware {name}")