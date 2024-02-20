import json
from abc import ABC

from src.abstractions import SequenceBuilder, ApplicationContext
from src.application import CommandPipeline


class RequestHandlerBase(ABC):

    def __init__(self, route_key: str,
                 sequence: SequenceBuilder,
                 command_pipeline: CommandPipeline):
        self.__command_pipeline = command_pipeline
        self.__route_key = route_key
        self.__sequence = sequence

    def run(self, event: dict) -> None:
        body = None
        auth_user_id = None
        parameters = {}
        if 'pathParameters' in event:
            path_parameters = event['pathParameters']
            if path_parameters is None:
                pass
            parameters = {**parameters, **path_parameters}
        if 'queryStringParameters' in event:
            query_parameters = event['queryStringParameters']
            if query_parameters is None:
                pass
            parameters = {**parameters, **query_parameters}
        try:
            auth_user_id = event['requestContext']['authorizer']['jwt']['claims']['name']
        except KeyError:
            pass
        if 'body' in event:
            try:
                json_body = json.loads(event['body'])
                body = json_body
            except ValueError:
                body = event['body']
        self.__command_pipeline.execute_commands(context=ApplicationContext(body=body,
                                                                            auth_user_id=auth_user_id,
                                                                            parameters=parameters,
                                                                            error_capsules=[]),
                                                 sequence=self.__sequence)
    
    @property
    def route_key(self) -> str:
        return self.__route_key
