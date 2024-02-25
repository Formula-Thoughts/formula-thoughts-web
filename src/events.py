from abc import ABC
from typing import Type

from src.abstractions import SequenceBuilder, Deserializer
from src.application import TopLevelSequenceRunner


class EventRunner:
    pass


class EventHandlerBase(ABC):

    def __init__(self, event: Type,
                 sequence: SequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer):
        self.__deserializer = deserializer
        self.__command_pipeline = command_pipeline
        self.__sequence = sequence
        self.__event = event

    def run(self, event: str):
        ...
