import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol
from unittest import TestCase

from formula_thoughts_web.abstractions import Command, ApplicationContext, Logger, SequenceBuilder, Deserializer, \
    ApiRequestHandler, Error, EventHandler
from formula_thoughts_web.application import FluentSequenceBuilder, TopLevelSequenceRunner, USE_RESPONSE_ERROR
from formula_thoughts_web.crosscutting import ObjectMapper
from formula_thoughts_web.events import EventHandlerBase, EVENT
from formula_thoughts_web.exceptions import MappingException
from formula_thoughts_web.ioc import register_web, Container, LambdaRunner
from formula_thoughts_web.web import ApiRequestHandlerBase

BAKING_ID = str(uuid.uuid4())


BAKING_ID_VAR = "BAKING_ID"
BAKING_REQUEST_VAR = "BAKING_REQUEST"


def register_dependencies(services: Container) -> None:
    (services.register(BakingService)
     .register(NotificationService)
     .register(CreateBreadRequestCommand, CreateWhiteBreadRequestCommand)
     .register(ValidateBreadRequestCommand, ValidateWhiteBreadRequestCommand)
     .register(CreateBreadCommand, CreateWhiteBreadCommand)
     .register(PublishBreadNotificationCommand, PublishWhiteBreadNotificationCommand)
     .register(CreateBreadSequenceBuilder, CreateWhiteBreadSequenceBuilder)
     .register(ApiRequestHandler, CreateBreadRequestHandler)
     .register_status_code_mappings({
        BreadResponse: 200,
        BreadValidationError: 400
     })
     .register(CreateBreadAsyncSequenceBuilder, CreateWhiteBreadAsyncSequenceBuilder)
     .register(CreateBreadAsyncCommand, CreateWhiteBreadAsyncCommand)
     .register(EventHandler, CreateBreadRequestEventHandler))


def handler(event, context) -> dict:
    ioc = Container()
    register_web(services=ioc, default_error_handling_strategy=USE_RESPONSE_ERROR)
    register_dependencies(services=ioc)
    lambda_runner = ioc.resolve(service=LambdaRunner)
    return lambda_runner.run(event=event, context=context)


@dataclass
class PreviousBake:
    id: str = None


@dataclass(unsafe_hash=True)
class BreadModel:
    temperature: Decimal = None
    yeast_g: float = None
    flour_g: float = None
    water_ml: float = None
    olive_oil_ml: float = None
    previous_bakes: list[PreviousBake] = field(default_factory=lambda: [])


@dataclass(unsafe_hash=True)
class BreadNotification:
    temperature: Decimal = None
    baking_id: str = None


class BakingService:

    def __init__(self, logger: Logger):
        self.__logger = logger

    def bake_bread(self, bread: BreadModel) -> str:
        self.__logger.log_info(message=f"baking bread at {bread.temperature} degrees")
        return BAKING_ID


class NotificationService:

    def __init__(self, logger: Logger):
        self.__logger = logger

    def publish(self, notif: dict) -> bool:
        self.__logger.log_info(message=f"raising notification {notif}")
        return True


class CreateBreadAsyncSequenceBuilder(SequenceBuilder, Protocol):
    pass


class CreateBreadSequenceBuilder(SequenceBuilder, Protocol):
    pass


class CreateBreadCommand(Command, Protocol):
    pass


class CreateBreadRequestCommand(Command, Protocol):
    pass


class ValidateBreadRequestCommand(Command, Protocol):
    pass


class PublishBreadNotificationCommand(Command, Protocol):
    pass


class CreateBreadAsyncCommand(Command, Protocol):
    pass


@dataclass
class BreadResponse:
    bread: BreadModel = None
    baking_id: str = None


class BreadValidationError(Error):
    pass


temperature_error = BreadValidationError(message="temperature has to be above 0c")
bread_mapping_validation_error = BreadValidationError(message="failed to map request")
yeast_error = BreadValidationError(message="yeast must be above 0g")
flour_error = BreadValidationError(message="flour must be above 0g")
water_error = BreadValidationError(message="water must be above 0ml")
oil_error = BreadValidationError(message="oil must be above 0ml")


class CreateWhiteBreadRequestCommand:

    def __init__(self,
                 mapper: ObjectMapper,
                 logger: Logger):
        self.__logger = logger
        self.__mapper = mapper

    def run(self, context: ApplicationContext) -> None:
        try:
            model = self.__mapper.map_from_dict(_from=context.body, to=BreadModel)
            context.set_var(BAKING_REQUEST_VAR, model)
            self.__logger.add_global_properties(properties={
                "temperature": model.temperature,
                "water": model.water_ml,
                "yeast": model.yeast_g,
                "oil": model.olive_oil_ml,
                "flour": model.flour_g
            })
        except MappingException as e:
            context.error_capsules.append(bread_mapping_validation_error)


class ValidateWhiteBreadRequestCommand:

    def run(self, context: ApplicationContext) -> None:
        request = context.get_var(BAKING_REQUEST_VAR, BreadModel)

        if request.temperature <= Decimal('0'):
            context.error_capsules.append(temperature_error)

        if request.yeast_g <= 0:
            context.error_capsules.append(yeast_error)

        if request.flour_g <= 0:
            context.error_capsules.append(flour_error)

        if request.water_ml <= 0:
            context.error_capsules.append(water_error)

        if request.olive_oil_ml <= 0:
            context.error_capsules.append(oil_error)


class CreateWhiteBreadCommand:

    def __init__(self, baking_service: BakingService):
        self.__baking_service = baking_service

    def run(self, context: ApplicationContext) -> None:
        bread = context.get_var(BAKING_REQUEST_VAR, BreadModel)
        _id = self.__baking_service.bake_bread(bread=bread)
        bread.previous_bakes.append(PreviousBake(id=_id))
        context.set_var(BAKING_ID_VAR, _id)
        context.response = BreadResponse(baking_id=_id, bread=bread)
        

class CreateWhiteBreadAsyncCommand:
    
    def __init__(self, baking_service: BakingService):
        self.__baking_service = baking_service
        
    def run(self, context: ApplicationContext) -> None:
        event = context.get_var(EVENT, BreadModel)

        if event.yeast_g <= 0:
            context.error_capsules.append(yeast_error)

        _id = self.__baking_service.bake_bread(context.get_var(EVENT, BreadModel))
        context.set_var(BAKING_ID_VAR, _id)


class PublishWhiteBreadNotificationCommand:

    def __init__(self, notification_service: NotificationService):
        self.__notification_service = notification_service

    def run(self, context: ApplicationContext) -> None:
        published = self.__notification_service.publish(
            notif=BreadNotification(temperature=context.get_var(BAKING_REQUEST_VAR, BreadModel).temperature,
                                    baking_id=context.get_var(BAKING_ID_VAR, str)).__dict__)


class CreateWhiteBreadAsyncSequenceBuilder(FluentSequenceBuilder):

    def __init__(self, create_bread_async_command: CreateBreadAsyncCommand):
        super().__init__()
        self.__create_bread_async_command = create_bread_async_command

    def build(self):
        self._add_command(command=self.__create_bread_async_command)


class CreateWhiteBreadSequenceBuilder(FluentSequenceBuilder):

    def __init__(self, create_bread_command: CreateBreadCommand,
                 publish_bread_notification: PublishBreadNotificationCommand,
                 create_bread_request: CreateBreadRequestCommand,
                 validate_bread_request: ValidateBreadRequestCommand):
        super().__init__()
        self.__validate_bread_request = validate_bread_request
        self.__create_bread_request = create_bread_request
        self.__publish_bread_notification = publish_bread_notification
        self.__create_bread_command = create_bread_command

    def build(self):
        self._add_command(command=self.__create_bread_request). \
            _add_command(command=self.__create_bread_command). \
            _add_command(command=self.__validate_bread_request). \
            _add_command(command=self.__publish_bread_notification)


class CreateBreadRequestHandler(ApiRequestHandlerBase):

    def __init__(self, sequence: CreateBreadSequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer,
                 logger: Logger):
        super().__init__("POST /bake-bread",
                         sequence,
                         command_pipeline,
                         deserializer,
                         logger)


class CreateBreadRequestEventHandler(EventHandlerBase):

    def __init__(self, sequence: CreateBreadAsyncSequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer,
                 object_mapper: ObjectMapper):
        super().__init__(BreadModel,
                         sequence,
                         command_pipeline,
                         deserializer,
                         object_mapper)


class TestExampleCode(TestCase):
        
    def test_run_api_request_handler(self):
        # arrange & act
        response = handler(event={"routeKey": "POST /bake-bread", "body": "{\"temperature\": 14.5, \"yeastG\": 24.5, \"flourG\": 546.4, \"waterMl\": 0.1, \"oliveOilMl\": 0.2}"}, context={})
        
        # assert
        with self.subTest(msg="assert response is OK"):
            self.assertEqual(response['statusCode'], 200)

        # assert
        with self.subTest(msg="assert body matches"):
            self.assertEqual(response['body'], "{\"bread\": {\"temperature\": 14.5, \"yeastG\": 24.5, \"flourG\": 546.4, \"waterMl\": 0.1, \"oliveOilMl\": 0.2, \"previousBakes\": [{\"id\": \""+BAKING_ID+"\"}]}, \"bakingId\": \""+BAKING_ID+"\"}")

    def test_run_api_request_handler_when_there_is_error(self):
        # arrange & act
        response = handler(event={"routeKey": "POST /bake-bread", "body": "{\"temperature\": 0, \"yeastG\": 24.5, \"flourG\": 546.4, \"waterMl\": 0.1, \"oliveOilMl\": 0.2}"},
                           context={})

        # assert
        with self.subTest(msg="assert response is bad request"):
            self.assertEqual(response['statusCode'], 400)

        # assert
        with self.subTest(msg="assert body matches"):
            self.assertEqual(response['body'], "{\"message\": \"temperature has to be above 0c\"}")

    def test_run_event_handler(self):
        # arrange & act
        response = handler(event={"Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "body": "{\"temperature\": 14.5, \"yeastG\": 24.5, \"flourG\": 546.4, \"waterMl\": 0.1, \"oliveOilMl\": 0.2}",
                "messageAttributes": {
                    "messageType": {
                        "dataType": "String",
                        "stringValue": "BreadModel"
                    }
                }
            }
        ]}, context={})

        # assert
        with self.subTest(msg="assert no failures occured"):
            self.assertEqual(response['batchItemFailures'], [])

    def test_run_event_handler_when_there_is_a_failiure(self):
        # arrange & act
        response = handler(event={"Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "body": "{\"temperature\": 54, \"yeastG\": 0, \"flourG\": 546.4, \"waterMl\": 0.1, \"oliveOilMl\": 0.2}",
                "messageAttributes": {
                    "messageType": {
                        "dataType": "String",
                        "stringValue": "BreadModel"
                    }
                }
            }
        ]}, context={})

        # assert
        with self.subTest(msg="assert 1 failure occured"):
            self.assertEqual(response['batchItemFailures'], [{"itemIdentifier": "059f36b4-87a3-44ab-83d2-661975830a7d"}])
        