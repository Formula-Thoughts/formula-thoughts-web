from unittest import TestCase

from src.application import Error, FluentSequenceBuilder, ApplicationContext, CommandPipeline, Response, \
    Command
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
        context.error_capsules.append(Error(msg="error", status_code=403))


class DummyNestedErrorSequenceBuilder(FluentSequenceBuilder):

    def __init__(self):
        super().__init__()

    def build(self):
        self._add_command(Command1())\
            ._add_command(CommandError())\
            ._add_command(Command3())


class DummyNested2SequenceBuilder(FluentSequenceBuilder):

    def __init__(self):
        super().__init__()

    def build(self):
        self._add_command(Command3())\
            ._add_command(Command4())\
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
        self._add_command(Command1())\
            ._add_sequence_builder(self.__sequence)\
            ._add_command(Command2())\
            ._add_command(Command3())


class TestSequenceBuilder(TestCase):

    def test_sequence(self):
        # arrange
        middleware = CommandPipeline(logger=logger_factory())
        sut = DummyNested2SequenceBuilder()
        context = ApplicationContext(body={"trail": []}, response=Response())

        # act
        middleware.execute_commands(context=context,
                                    sequence=sut)

        # assert
        self.assertEqual(context.body["trail"], ["command 3", "command 4", "command 5"])

    def test_sequence_with_short_circuit(self):
        # arrange
        middleware = CommandPipeline(logger=logger_factory())
        sut = DummyNestedErrorSequenceBuilder()
        context = ApplicationContext(body={"trail": []}, response=Response())

        # act
        middleware.execute_commands(context=context,
                                    sequence=sut)

        # assert
        with self.subTest("invocations match"):
            self.assertEqual(context.body["trail"], ["command 1"])

        # assert
        with self.subTest("context is updated"):
            self.assertEqual(context.response.body, {"message": "error"})
            self.assertEqual(context.response.status_code, 403)


class TestComplexSequenceBuilder(TestCase):

    def setUp(self) -> None:
        self.__sut = DummySequenceBuilder(sequence=DummyNestedSequenceBuilder(
                                              sequence=DummyNested2SequenceBuilder()))
        self.__middleware = CommandPipeline(logger=logger_factory())

    def test_build_and_run_sequence(self):
        # act
        context = ApplicationContext(body={"trail": []}, response=Response())
        self.__middleware.execute_commands(context=context,
                                           sequence=self.__sut)

        # assert
        with self.subTest(msg="invocations match list"):
            self.assertEqual(context.body["trail"], ["command 1", "command 3", "command 4", "command 5", "command 2", "command 3"])