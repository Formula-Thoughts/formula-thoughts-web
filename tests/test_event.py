from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import Mock, MagicMock, call

from src.abstractions import SequenceBuilder, Deserializer, ApplicationContext, EventHandler
from src.application import TopLevelSequenceRunner
from src.crosscutting import JsonCamelToSnakeDeserializer, ObjectMapper
from src.events import EventHandlerBase, EventRunner


@dataclass(unsafe_hash=True)
class Model:
    test_prop_1: int = None
    test_prop_2: str = None


class ExampleEventHandler(EventHandlerBase):

    def __init__(self,
                 mock_sequence: SequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer,
                 object_mapper: ObjectMapper) -> None:
        super().__init__(event=Model,
                         sequence=mock_sequence,
                         command_pipeline=command_pipeline,
                         deserializer=deserializer,
                         object_mapper=object_mapper)


class TestEventHandler(TestCase):

    def setUp(self):
        self.__command_pipeline: TopLevelSequenceRunner = Mock()
        self.__mock_sequence: SequenceBuilder = Mock()
        self.__sut = ExampleEventHandler(mock_sequence=self.__mock_sequence,
                                         command_pipeline=self.__command_pipeline,
                                         deserializer=JsonCamelToSnakeDeserializer(),
                                         object_mapper=ObjectMapper())

    def test_run(self):
        # arrange
        self.__command_pipeline.run = MagicMock()

        # act
        self.__sut.run(event="{\"testProp1\": 4, \"testProp2\": \"test\"}")

        # assert
        with self.subTest(msg="assert event pipeline is run once"):
            self.__command_pipeline.run.assert_called_once()

        # assert
        with self.subTest(msg="assert event pipeline is run with top level sequence"):
            self.__command_pipeline.run.assert_called_with(context=ApplicationContext(
                body={"test_prop_1": 4, "test_prop_2": "test"},
                variables={"EVENT": Model(test_prop_1=4, test_prop_2="test")},
                error_capsules=[]
            ), top_level_sequence=self.__mock_sequence)
            
            
class TestEventRunner(TestCase):
    
    def setUp(self):
        self.__event_handler: EventHandler = Mock()
        self.__event_handlers = [self.__event_handler]
        self.__sut = EventRunner(event_handlers=self.__event_handlers,
                                 logger=Mock())

    def test_run(self):
        # arrange
        self.__event_handler.event_type = Model
        self.__event_handler.run = MagicMock()

        # act
        message1 = "{\"testProp1\": 4, \"testProp2\": \"test\"}"
        message2 = "{\"testProp1\": 5, \"testProp2\": \"test 2\"}"
        self.__sut.run(event={
            "Records": [
                {
                    "body": message1,
                    "messageAttributes": {
                        "messageType": {
                            "dataType": "String",
                            "stringValue": "tests.test_event.Model"
                        }
                    }
                },
                {
                    "body": message2,
                    "messageAttributes": {
                        "messageType": {
                            "dataType": "String",
                            "stringValue": "tests.test_event.Model"
                        }
                    }
                }
            ]
        })

        # assert
        with self.subTest(msg="request handler was run twice"):
            self.__event_handler.run.assert_has_calls(calls=[
                call(message1),
                call(message2)
            ])