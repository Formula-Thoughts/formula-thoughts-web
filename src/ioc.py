from typing import TypeVar, Type, Any

import punq

from src.abstractions import Serializer, Deserializer, Logger
from src.application import TopLevelSequenceRunner, ErrorHandlingTypeState
from src.crosscutting import JsonSnakeToCamelSerializer, JsonCamelToSnakeDeserializer, ObjectMapper, JsonConsoleLogger
from src.events import EventRunner
from src.exceptions import EventSchemaInvalidException
from src.web import WebRunner, StatusCodeMapping


T = TypeVar('T')


class LambdaRunner:
    
    def __init__(self, web_runner: WebRunner,
                 event_runner: EventRunner):
        self.__event_runner = event_runner
        self.__web_runner = web_runner
        
    def run(self, event: dict, context: dict) -> dict:
        # TODO: improve validation, use information from context about request
        if 'routeKey' in event:
            return self.__web_runner.run(event=event)
        elif 'Records' in event:
            return self.__event_runner.run(event=event)
        else:
            raise EventSchemaInvalidException("schema does not match SQS event or API gateway")


class Container:

    def __init__(self):
        self.__container = punq.Container()

    def register(self, service: Type[T], implementation: Type[T] = None, scope: punq.Scope = punq.Scope.singleton) -> 'Container':
        if implementation is None:
            self.__container.register(service=service, factory=punq.empty, scope=scope)
        else:
            self.__container.register(service, implementation, scope=scope)
        return self

    def resolve(self, service: Type[T]) -> T:
        return self.__container.resolve(service)

    def register_status_code_mappings(self, mappings: dict) -> 'Container':
        self.__container.register(service=StatusCodeMapping, scope=punq.Scope.singleton)
        status_mapping: StatusCodeMapping = self.__container.resolve(StatusCodeMapping)
        for code in mappings.keys():
            status_mapping.add_mapping(_type=code, status_code=mappings[code])
        return self


def register_web(services: Container):
    services.register(service=ErrorHandlingTypeState, scope=punq.Scope.singleton)
    services.register(service=LambdaRunner)
    services.register(service=EventRunner)
    services.register(service=Serializer, implementation=JsonSnakeToCamelSerializer)
    services.register(service=Deserializer, implementation=JsonCamelToSnakeDeserializer)
    services.register(service=TopLevelSequenceRunner)
    services.register(service=WebRunner)
    services.register(service=ObjectMapper)
    services.register(service=Logger, implementation=JsonConsoleLogger)
    services.register(service=StatusCodeMapping, scope=punq.Scope.singleton)
