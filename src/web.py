from abc import ABC

from src.abstractions import SequenceBuilder
from src.application import CommandPipeline


class RequestHandlerBase(ABC):

    def __init__(self, route_key: str,
                 sequence: SequenceBuilder,
                 command_pipeline: CommandPipeline):
        self.__command_pipeline = command_pipeline
        self.__route_key = route_key
        self.__sequence = sequence

    def run(self, event: dict) -> None:
        ...
    
    @property
    def route_key(self) -> str:
        return self.__route_key
