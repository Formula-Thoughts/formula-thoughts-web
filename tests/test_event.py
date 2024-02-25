from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from src.abstractions import SequenceBuilder, Deserializer, ApplicationContext
from src.application import TopLevelSequenceRunner
from src.crosscutting import JsonCamelToSnakeDeserializer
from src.event import EventHandlerBase


@dataclass(unsafe_hash=True)
class Model:
    test_prop_1: int = None
    test_prop_2: str = None


class EventHandler(EventHandlerBase):

    def __init__(self,
                 mock_sequence: SequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer):
        super().__init__(Model,
                         mock_sequence,
                         command_pipeline,
                         deserializer)


class TestEventHandler(TestCase):

    def setUp(self):
        self.__command_pipeline: TopLevelSequenceRunner = Mock()
        self.__mock_sequence: SequenceBuilder = Mock()
        self.__sut = EventHandler(mock_sequence=self.__mock_sequence,
                                  command_pipeline=self.__command_pipeline,
                                  deserializer=JsonCamelToSnakeDeserializer())

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