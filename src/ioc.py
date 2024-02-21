import punq

from src.abstractions import Serializer, Deserializer
from src.application import TopLevelSequenceRunner
from src.crosscutting import JsonSnakeToCamelSerializer, JsonCamelToSnakeDeserializer
from src.web import WebRunner, StatusCodeMapping


def register_web(services: punq.Container):
    services.register(Serializer, JsonSnakeToCamelSerializer)
    services.register(Deserializer, JsonCamelToSnakeDeserializer)
    services.register(TopLevelSequenceRunner)
    services.register(WebRunner)
    services.register(StatusCodeMapping, scope=punq.Scope.singleton)


def add_status_code_mappings(services: punq.Container, mappings: dict):
    status_mapping: StatusCodeMapping = services.resolve(StatusCodeMapping)
    for code in mappings.keys():
        status_mapping.add_mapping(type=code, status_code=mappings[code])
