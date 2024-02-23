from typing import TypeVar, Type

import punq

from src.abstractions import Serializer, Deserializer
from src.application import TopLevelSequenceRunner
from src.crosscutting import JsonSnakeToCamelSerializer, JsonCamelToSnakeDeserializer, ObjectMapper
from src.web import WebRunner, StatusCodeMapping


T = TypeVar('T')


class Container:

    def __init__(self):
        self.__container = punq.Container()

    def register(self, service: Type[T], implementation: Type[T] = None, scope: punq.Scope = punq.Scope.singleton) -> 'Container':
        if implementation is None:
            self.__container.register(service, scope=scope)
        self.__container.register(service, implementation, scope=scope)
        return self

    def resolve(self, service: Type[T]) -> T:
        return self.__container.resolve(service)


def register_web(services: Container):
    services.register(Serializer, JsonSnakeToCamelSerializer)
    services.register(Deserializer, JsonCamelToSnakeDeserializer)
    services.register(TopLevelSequenceRunner)
    services.register(WebRunner)
    services.register(ObjectMapper)
    services.register(StatusCodeMapping, scope=punq.Scope.singleton)


def add_status_code_mappings(services: punq.Container, mappings: dict):
    status_mapping: StatusCodeMapping = services.resolve(StatusCodeMapping)
    for code in mappings.keys():
        status_mapping.add_mapping(type=code, status_code=mappings[code])


