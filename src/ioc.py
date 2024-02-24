from typing import TypeVar, Type, Any

import punq

from src.abstractions import Serializer, Deserializer, Logger
from src.application import TopLevelSequenceRunner
from src.crosscutting import JsonSnakeToCamelSerializer, JsonCamelToSnakeDeserializer, ObjectMapper, JsonConsoleLogger
from src.web import WebRunner, StatusCodeMapping


T = TypeVar('T')


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

    def register_status_code_mappings(self, mappings: dict):
        self.__container.register(service=StatusCodeMapping, scope=punq.Scope.singleton)
        status_mapping: StatusCodeMapping = self.__container.resolve(StatusCodeMapping)
        for code in mappings.keys():
            status_mapping.add_mapping(_type=code, status_code=mappings[code])


def register_web(services: Container):
    services.register(service=Serializer, implementation=JsonSnakeToCamelSerializer)
    services.register(service=Deserializer, implementation=JsonCamelToSnakeDeserializer)
    services.register(service=TopLevelSequenceRunner)
    services.register(service=WebRunner)
    services.register(service=ObjectMapper)
    services.register(service=Logger, implementation=JsonConsoleLogger)
    services.register(service=StatusCodeMapping, scope=punq.Scope.singleton)


