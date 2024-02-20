import json
from abc import ABC

from src.abstractions import SequenceBuilder, ApplicationContext, RequestHandler, Serializer
from src.application import CommandPipeline


class WebRunner:

    def __init__(self,
                 request_handlers: list[RequestHandler],
                 serializer: Serializer):
        self.__serializer = serializer
        self.__request_handlers = request_handlers

    def run(self, event) -> dict:
        # request_handler_matches = filter(lambda x: x.route_key == event['routeKey'], self.__request_handlers)
        # if request_handler_matches ==
        # context: ApplicationContext = request_handler_matches[0](event=event)
        ...


class RequestHandlerBase(ABC):

    def __init__(self, route_key: str,
                 sequence: SequenceBuilder,
                 command_pipeline: CommandPipeline):
        self.__command_pipeline = command_pipeline
        self.__route_key = route_key
        self.__sequence = sequence

    def run(self, event: dict) -> ApplicationContext:
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
        context = ApplicationContext(body=body,
                                     auth_user_id=auth_user_id,
                                     parameters=parameters,
                                     error_capsules=[])
        self.__command_pipeline.execute_commands(context=context,
                                                 sequence=self.__sequence)
        return context

    @property
    def route_key(self) -> str:
        return self.__route_key
