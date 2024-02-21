import punq

from src.abstractions import Serializer, Deserializer
from src.application import TopLevelSequenceRunner
from src.crosscutting import JsonSnakeToCamelSerializer, JsonCamelToSnakeDeserializer
from src.web import WebRunner


def register_web(services: punq.Container):
    services.register(Serializer, JsonSnakeToCamelSerializer)
    services.register(Deserializer, JsonCamelToSnakeDeserializer)
    services.register(TopLevelSequenceRunner)
    services.register(WebRunner)