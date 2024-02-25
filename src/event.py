from abc import ABC
from typing import Type

from src.abstractions import SequenceBuilder, Deserializer, ApplicationContext
from src.application import TopLevelSequenceRunner
from src.crosscutting import ObjectMapper

EVENT = "EVENT"


class EventRunner:
    pass


class EventHandlerBase(ABC):

    def __init__(self, event: Type,
                 sequence: SequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer,
                 object_mapper: ObjectMapper):
        self.__object_mapper = object_mapper
        self.__deserializer = deserializer
        self.__command_pipeline = command_pipeline
        self.__sequence = sequence
        self.__event = event

    def run(self, event: str):
        event_dict = self.__deserializer.deserialize(event)
        event_object = self.__object_mapper.map_from_dict(_from=event_dict, to=self.__event)
        self.__command_pipeline.run(context=ApplicationContext(body=event_dict,
                                                               variables={EVENT: event_object},
                                                               error_capsules=[]),
                                    top_level_sequence=self.__sequence)
