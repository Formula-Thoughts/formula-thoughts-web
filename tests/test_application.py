from unittest import TestCase
from unittest.mock import Mock, MagicMock

from src.abstractions import Error, ErrorHandlingStrategy
from src.application import FluentSequenceBuilder, ApplicationContext, TopLevelSequenceRunner, \
    Command, ErrorHandlingStrategyFactory
from tests import logger_factory


class Command1(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 1")


class Command2(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 2")


class Command3(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 3")


class Command4(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 4")


class Command5(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 5")


class CommandError(Command):

    def run(self, context: ApplicationContext):
        context.error_capsules.append(Error(message="error"))


class DummyNestedErrorSequenceBuilder(FluentSequenceBuilder):

    def __init__(self):
        super().__init__()

    def build(self):
        self._add_command(Command1()) \
            ._add_command(CommandError()) \
            ._add_command(Command3())


class DummyNested2SequenceBuilder(FluentSequenceBuilder):

    def __init__(self):
        super().__init__()

    def build(self):
        self._add_command(Command3()) \
            ._add_command(Command4()) \
            ._add_command(Command5())


class DummyNestedSequenceBuilder(FluentSequenceBuilder):

    def __init__(self, sequence: DummyNested2SequenceBuilder):
        super().__init__()
        self.__sequence = sequence

    def build(self):
        self._add_sequence_builder(self.__sequence)


class DummySequenceBuilder(FluentSequenceBuilder):

    def __init__(self, sequence: DummyNestedSequenceBuilder):
        super().__init__()
        self.__sequence = sequence

    def build(self):
        self._add_command(Command1()) \
            ._add_sequence_builder(self.__sequence) \
            ._add_command(Command2()) \
            ._add_command(Command3())


class TestSequenceBuilder(TestCase):

    def setUp(self):
        self.__error_handling_strategy_factory: ErrorHandlingStrategyFactory = Mock()
        self.__error_handling_strategy: ErrorHandlingStrategy = Mock()
        self.__top_level_sequence_runner = TopLevelSequenceRunner(logger=logger_factory(),
                                                                  error_handling_strategy_factory=self.__error_handling_strategy_factory)

    def test_sequence(self):
        # arrange
        sut = DummyNested2SequenceBuilder()
        self.__error_handling_strategy_factory.get_error_handling_strategy = MagicMock(
            return_value=self.__error_handling_strategy)
        context = ApplicationContext(body={"trail": []})

        # act
        self.__top_level_sequence_runner.run(context=context,
                                             top_level_sequence=sut)

        # assert
        self.assertEqual(context.body["trail"], ["command 3", "command 4", "command 5"])

    def test_sequence_with_short_circuit(self):
        # arrange
        sut = DummyNestedErrorSequenceBuilder()
        self.__error_handling_strategy.handle_error = MagicMock()
        self.__error_handling_strategy_factory.get_error_handling_strategy = MagicMock(
            return_value=self.__error_handling_strategy)
        context = ApplicationContext(body={"trail": []})

        # act
        self.__top_level_sequence_runner.run(context=context,
                                             top_level_sequence=sut)

        # assert
        with self.subTest("invocations match"):
            self.assertEqual(context.body["trail"], ["command 1"])

        # assert
        with self.subTest("error is handled once"):
            self.__error_handling_strategy.handle_error.assert_called_once()

        # assert
        with self.subTest("error is handled with correct args"):
            self.__error_handling_strategy.handle_error.assert_called_with(context=context,
                                                                           error=Error(message="error"))


class TestComplexSequenceBuilder(TestCase):

    def setUp(self) -> None:
        self.__sut = DummySequenceBuilder(sequence=DummyNestedSequenceBuilder(
            sequence=DummyNested2SequenceBuilder()))
        self.__error_handling_strategy: ErrorHandlingStrategy = Mock()
        self.__error_handling_strategy_factory: ErrorHandlingStrategyFactory = Mock()
        self.__top_level_sequence_runner = TopLevelSequenceRunner(logger=logger_factory(),
                                                                  error_handling_strategy_factory=self.__error_handling_strategy_factory)

    def test_build_and_run_sequence(self):
        # arrange
        context = ApplicationContext(body={"trail": []})
        self.__error_handling_strategy_factory.get_error_handling_strategy = MagicMock(
            return_value=self.__error_handling_strategy)

        # act
        self.__top_level_sequence_runner.run(context=context,
                                             top_level_sequence=self.__sut)

        # assert
        with self.subTest(msg="invocations match list"):
            self.assertEqual(context.body["trail"],
                             ["command 1", "command 3", "command 4", "command 5", "command 2", "command 3"])
