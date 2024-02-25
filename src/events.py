import typing
from abc import ABC
from typing import Type

from src.abstractions import SequenceBuilder, Deserializer, ApplicationContext, EventHandler, Logger
from src.application import TopLevelSequenceRunner
from src.crosscutting import ObjectMapper
from src.exceptions import EventNotFoundException

EVENT = "EVENT"


class EventRunner:

    def __init__(self, event_handlers: list[EventHandler],
                 logger: Logger):
        self.__logger = logger
        self.__event_handlers = event_handlers

    def run(self, event: dict):
        try:
            for message in event['Records']:
                event_type = message['messageAttributes']['messageType']['stringValue']
                body = message['body']
                self.__logger.add_global_properties(properties={"event_type": event_type})
                watch = self.__event_handlers
                matching_handlers = list(filter(lambda x: f"{x.event_type.__name__}" == event_type, self.__event_handlers))
                if len(matching_handlers) is 0:
                    raise EventNotFoundException(f"{event_type} does not match any found handlers")
                matching_handlers[0].run(event=body)
        except Exception as e:
            self.__logger.log_error(message="event runner captured exception")
            self.__logger.log_exception(exception=e)
            raise e


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

    @property
    def event_type(self) -> typing.Type:
        return self.__event
