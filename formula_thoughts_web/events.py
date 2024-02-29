import typing
import uuid
from abc import ABC
from typing import Type

from botocore.client import BaseClient

from formula_thoughts_web.abstractions import SequenceBuilder, Deserializer, ApplicationContext, EventHandler, Logger, \
    Serializer
from formula_thoughts_web.application import TopLevelSequenceRunner, ErrorHandlingTypeState, USE_EXCEPTION_ERROR
from formula_thoughts_web.crosscutting import ObjectMapper
from formula_thoughts_web.exceptions import EventNotFoundException

EVENT = "EVENT"


class SQSEventPublisher:

    def __init__(self, sqs_client: BaseClient,
                 queue_name: str,
                 serializer: Serializer,
                 mapper: ObjectMapper):
        self.__mapper = mapper
        self.__serializer = serializer
        self.__sqs_client = sqs_client
        url = self.__sqs_client.get_queue_url(QueueName=queue_name)
        self.__queue_url = url["QueueUrl"]

    def send_sqs_message(self, message_group_id, payload: typing.Any):
        self.__sqs_client.send_message(
            QueueUrl=str(self.__queue_url),
            MessageBody=self.__serializer.serialize(data=self.__mapper.map_to_dict(_from=payload,
                                                                                   to=type(payload))),
            MessageGroupId=message_group_id,
            MessageAttributes={
                'messageType': {
                    'StringValue': type(payload).__name__,
                    'DataType': 'String'
                }
            },
            MessageDeduplicationId=str(uuid.uuid4())
        )


class EventRunner:

    def __init__(self, event_handlers: list[EventHandler],
                 error_handling_state: ErrorHandlingTypeState,
                 logger: Logger):
        self.__error_handling_state = error_handling_state
        self.__logger = logger
        self.__event_handlers = event_handlers

    def run(self, event: dict):
        failed_messages = []
        try:
            self.__error_handling_state.error_handling_type = USE_EXCEPTION_ERROR
            for message in event['Records']:
                try:
                    event_type = message['messageAttributes']['messageType']['stringValue']
                    body = message['body']
                    self.__logger.add_global_properties(properties={"event_type": event_type})
                    matching_handlers = list(filter(lambda x: f"{x.event_type.__name__}" == event_type, self.__event_handlers))
                    if len(matching_handlers) == 0:
                        raise EventNotFoundException(f"{event_type} does not match any found handlers")
                    matching_handlers[0].run(event=body)
                except Exception as e:
                    self.__logger.log_error(message="event runner captured exception")
                    self.__logger.log_exception(exception=e)
                    failed_messages.append(message["messageId"])
        except Exception as e:
            self.__logger.log_error(message="fatal error in event handler, retrying entire batch")
            self.__logger.log_exception(exception=e)
            raise
        return {
            'batchItemFailures': list(map(lambda x: {'itemIdentifier': x}, failed_messages))
        }


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
