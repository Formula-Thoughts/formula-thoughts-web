import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import get_args, Union
from unittest import TestCase

import ddt
from autofixture import AutoFixture

from formula_thoughts_web.crosscutting import ObjectMapper, JsonCamelToSnakeDeserializer, JsonSnakeToCamelSerializer

TEST_DICT_JSON = "{\"name\": \"adam raymond\", \"snakeInValue\": \"snake_in_value\", \"value2To3Values\": 2, \"yeastG\": 24.2}"
TEST_LIST_SERIALIZATION_JSON = "[{\"name\": \"adam raymond\", \"snakeInValue\": \"snake_in_value\", \"value2To3Values\": 2}, {\"name\": \"adam raymond\", \"snakeInValue\": \"snake_in_value\", \"value2To3Values\": 2}, {\"name\": \"adam raymond\", \"snakeInValue\": \"snake_in_value\", \"value2To3Values\": 2}]"
TEST_LIST_SERIALIZATION_EMPTY_JSON = "[]"
TEST_DICT_NESTED_JSON = "{\"name\": \"adam raymond\", \"snakeInValue\": \"snake_in_value\", \"value2To3Values\": 2, \"nestedObject\": {\"name\": \"dennis reynolds\", \"snakeValue\": 3}, \"arrayValue\": [\"apples\", \"pears\", \"oranges\"]}"
TEST_DICT_JSON_WITH_CAPS_KEY = "{\"yeastG\": 24.2, \"name\": \"adam raymond\", \"snakeInValue\": \"snake_in_value\", \"value2To3Values\": 2, \"capitalLETTERSValue\": 1}"
TEST_DICT_WITH_ENUM_JSON = "{\"name\": \"adam raymond\", \"enum\": \"VALUE1\"}"
TEST_DICT_WITH_ENUM_LIST_JSON = "{\"name\": \"adam raymond\", \"enum\": [\"VALUE1\", \"VALUE2\"]}"
TEST_LIST_OF_DICTS_WITH_ENUM_JSON = "[{\"name\": \"adam raymond\", \"enum\": \"VALUE1\"}, {\"name\": \"adam raymond\", \"enum\": \"VALUE2\"}]"
TEST_LIST_OF_DICTS_WITH_ENUM_LIST_JSON = "[{\"name\": \"adam raymond\", \"enum\": [\"VALUE1\", \"VALUE2\"]}, {\"name\": \"adam raymond\", \"enum\": [\"VALUE1\", \"VALUE2\"]}]"


TEST_DICT = {
    "name": "adam raymond",
    "snake_in_value": "snake_in_value",
    "value_2_to_3_values": 2,
    "yeast_g": 24.2
}

TEST_LIST_SERIALIZATION_EMPTY = []

TEST_LIST_SERIALIZATION = [{
    "name": "adam raymond",
    "snake_in_value": "snake_in_value",
    "value_2_to_3_values": 2
}, {
    "name": "adam raymond",
    "snake_in_value": "snake_in_value",
    "value_2_to_3_values": 2
}, {
    "name": "adam raymond",
    "snake_in_value": "snake_in_value",
    "value_2_to_3_values": 2
}]

TEST_NESTED_DICT = {
    "name": "adam raymond",
    "snake_in_value": "snake_in_value",
    "value_2_to_3_values": 2,
    "nested_object": {
        "name": "dennis reynolds",
        "snake_value": 3
    },
    "array_value": ["apples", "pears", "oranges"]
}

TEST_DICT_WITH_CAPS_KEY = {
    "yeast_g": 24.2,
    "name": "adam raymond",
    "snake_in_value": "snake_in_value",
    "value_2_to_3_values": 2,
    "capital_letters_value": 1
}


class TestEnum(Enum):
    VALUE1 = "VALUE1"
    VALUE2 = "VALUE2"


TEST_DICT_WITH_ENUM = {
    "name": "adam raymond",
    "enum": TestEnum.VALUE1
}


TEST_DICT_WITH_ENUM_LIST = {
    "name": "adam raymond",
    "enum": [TestEnum.VALUE1, TestEnum.VALUE2]
}


TEST_LIST_OF_DICTS_WITH_ENUM = [
    {
        "name": "adam raymond",
        "enum": TestEnum.VALUE1
    },
    {
        "name": "adam raymond",
        "enum": TestEnum.VALUE2
    }
]


TEST_LIST_OF_DICTS_WITH_ENUM_LIST = [
    {
        "name": "adam raymond",
        "enum": [TestEnum.VALUE1, TestEnum.VALUE2]
    },
    {
        "name": "adam raymond",
        "enum": [TestEnum.VALUE1, TestEnum.VALUE2]
    }
]


@dataclass(unsafe_hash=True)
class InheritedDto:
    id: str = field(default_factory=lambda: "default_id")
    name: str = None


@dataclass(unsafe_hash=True)
class NestedNestedTestOtherDto:
    id: str = None
    name: str = None


@dataclass(unsafe_hash=True)
class NestedTestOtherDto:
    id: str = None
    name: str = None
    list_of_nested: list[NestedNestedTestOtherDto] = None
    nested: NestedNestedTestOtherDto = None


@dataclass(unsafe_hash=True)
class TestOtherDto:
    id: str = None
    name: str = None
    bool_: bool = None
    enum: TestEnum = None
    list_of_enums: list[TestEnum] = None
    list_of_strings: list[str] = None
    list_of_ints: list[int] = None
    list_of_floats: list[float] = None
    list_of_bools: list[bool] = None
    date: datetime.datetime = None
    list_of_dates: list[datetime.datetime] = None
    decimal_num: float = None
    nested: NestedTestOtherDto = None
    nested_list: list[NestedTestOtherDto] = None


@dataclass(unsafe_hash=True)
class NestedNestedTestDto:
    id: str = None
    name: str = None


@dataclass(unsafe_hash=True)
class NestedTestDto:
    id: str = None
    name: str = None
    list_of_nested: list[NestedNestedTestDto] = None
    nested: NestedNestedTestDto = None


@dataclass(unsafe_hash=True)
class TestDto(InheritedDto):
    bool_: bool = None
    enum: TestEnum = None
    list_of_enums: list[TestEnum] = None
    list_of_strings: list[str] = None
    list_of_ints: list[int] = None
    list_of_floats: list[float] = None
    list_of_bools: list[bool] = None
    date: datetime.datetime = None
    list_of_dates: list[datetime.datetime] = None
    decimal_num: float = None
    nested: NestedTestDto = None
    nested_list: list[NestedTestDto] = None


class TestMapper(TestCase):

    def test_map(self):
        # arrange
        test_dto = AutoFixture().create(dto=TestDto,
                                        list_limit=5,
                                        seed="1234",
                                        num=1)

        # act
        test_other_dto: TestOtherDto = ObjectMapper().map(_from=test_dto, to=TestOtherDto)

        # assert
        with self.subTest(msg="id with default value matches"):
            self.assertEqual(test_other_dto.id, "default_id")

        # assert
        with self.subTest(msg="date field matches"):
            self.assertEqual(test_other_dto.date, test_dto.date)

        # assert
        with self.subTest(msg="list of dates field matches"):
            self.assertEqual(test_other_dto.list_of_dates, test_dto.list_of_dates)

        # assert
        with self.subTest(msg="name field matches"):
            self.assertEqual(test_other_dto.name, test_dto.name)

        # assert
        with self.subTest(msg="nested list types match"):
            self.assertEqual(get_args(list[NestedTestOtherDto])[0], type(test_other_dto.nested_list[0]))

        # assert
        with self.subTest(msg="nested list lengths match"):
            self.assertEqual(len(test_dto.nested_list), len(test_other_dto.nested_list))

        # assert
        with self.subTest(msg="nested list field matches"):
            for i in range(0, len(test_other_dto.nested_list)):
                self.assertEqual(test_other_dto.nested_list[i].id, test_dto.nested_list[i].id)
                self.assertEqual(test_other_dto.nested_list[i].name, test_dto.nested_list[i].name)
                self.assertEqual(test_other_dto.nested_list[i].nested.name, test_dto.nested_list[i].nested.name)
                self.assertEqual(test_other_dto.nested_list[i].nested.id, test_dto.nested_list[i].nested.id)
                for j in range(0, len(test_other_dto.nested_list[i].list_of_nested)):
                    self.assertEqual(test_other_dto.nested_list[i].list_of_nested[j].id, test_dto.nested_list[i].list_of_nested[j].id)
                    self.assertEqual(test_other_dto.nested_list[i].list_of_nested[j].name, test_dto.nested_list[i].list_of_nested[j].name)

        # assert
        with self.subTest(msg="nested id field matches"):
            assert test_other_dto.nested.id == test_dto.nested.id

        # assert
        with self.subTest(msg="nested name field matches"):
            assert test_other_dto.nested.name == test_dto.nested.name

        # assert
        with self.subTest(msg="list of dates field matches"):
            assert test_other_dto.list_of_dates == test_dto.list_of_dates

        # assert
        with self.subTest(msg="list of bools field matches"):
            assert test_other_dto.list_of_bools == test_dto.list_of_bools

        # assert
        with self.subTest(msg="list of ints field matches"):
            assert test_other_dto.list_of_ints == test_dto.list_of_ints

        # assert
        with self.subTest(msg="bool field matches"):
            assert test_other_dto.bool_ == test_dto.bool_

        # assert
        with self.subTest(msg="list of strings field matches"):
            assert test_other_dto.list_of_strings == test_dto.list_of_strings

        # assert
        with self.subTest(msg="list of enums field matches"):
            assert test_other_dto.list_of_enums == test_dto.list_of_enums

        # assert
        with self.subTest(msg="enum field matches"):
            assert test_other_dto.enum == test_dto.enum

        # assert
        with self.subTest(msg="decimal field matches"):
            assert test_other_dto.decimal_num == test_dto.decimal_num

        # assert
        with self.subTest(msg="list of floats field matches"):
            assert test_other_dto.list_of_floats == test_dto.list_of_floats

    def test_map_from_dict(self):
        # arrange
        test_dict = {"nested": {"name": "John", "id": "test_id", "list_of_nested": [{"name": "Jane", "id": "test_id2"}]}}

        # act
        test_other_dto: TestOtherDto = ObjectMapper().map_from_dict(_from=test_dict, to=TestOtherDto)

        # assert
        with self.subTest(msg="assert nested property is set"):
            self.assertEqual(test_other_dto.nested.list_of_nested[0].name, "Jane")


@ddt.ddt
class TestJsonSnakeToCamelSerializer(TestCase):

    def setUp(self):
        self.__json_snake_to_camel_serializer = JsonSnakeToCamelSerializer()

    def test_serialize(self):
        # arrange
        input_data = TEST_DICT
        expected = TEST_DICT_JSON

        # act
        actual = self.__json_snake_to_camel_serializer.serialize(input_data)

        # assert
        self.assertEqual(actual, expected)

    @ddt.data((TEST_DICT_WITH_ENUM, TEST_DICT_WITH_ENUM_JSON),
          (TEST_DICT_WITH_ENUM_LIST, TEST_DICT_WITH_ENUM_LIST_JSON),
          (TEST_LIST_OF_DICTS_WITH_ENUM, TEST_LIST_OF_DICTS_WITH_ENUM_JSON),
          (TEST_LIST_OF_DICTS_WITH_ENUM_LIST, TEST_LIST_OF_DICTS_WITH_ENUM_LIST_JSON))
    def test_serialize_with_enum(self, data: tuple[Union[list, dict], str]):
        # arrange
        (input_data, expected) = data

        # act
        actual = self.__json_snake_to_camel_serializer.serialize(input_data)

        # assert
        self.assertEqual(actual, expected)

    def test_serialize_nested(self):
        # arrange
        input_data = TEST_NESTED_DICT
        expected = TEST_DICT_NESTED_JSON

        # act
        actual = self.__json_snake_to_camel_serializer.serialize(input_data)

        # assert
        self.assertEqual(actual, expected)

    def test_serialize_collection(self):
        # arrange
        input_data = TEST_LIST_SERIALIZATION
        expected = TEST_LIST_SERIALIZATION_JSON

        # act
        actual = self.__json_snake_to_camel_serializer.serialize(input_data)

        # assert
        self.assertEqual(actual, expected)

    def test_serialize_collection_empty(self):
        # arrange
        input_data = TEST_LIST_SERIALIZATION_EMPTY
        expected = TEST_LIST_SERIALIZATION_EMPTY_JSON

        # act
        actual = self.__json_snake_to_camel_serializer.serialize(input_data)

        # assert
        self.assertEqual(actual, expected)


class TestJsonCamelToSnakeCaseDeserializer(TestCase):

    def setUp(self):
        self.__json_camel_to_snake_case_deserializer = JsonCamelToSnakeDeserializer()

    def test_deserialize(self):
        # arrange
        expected = TEST_DICT_WITH_CAPS_KEY
        input_data = TEST_DICT_JSON_WITH_CAPS_KEY

        # act
        actual = self.__json_camel_to_snake_case_deserializer.deserialize(input_data)

        # assert
        self.assertEqual(actual, expected)

    def test_deserialize_nested(self):
        # arrange
        expected = TEST_NESTED_DICT
        input_data = TEST_DICT_NESTED_JSON

        # act
        actual = self.__json_camel_to_snake_case_deserializer.deserialize(input_data)

        # assert
        self.assertEqual(actual, expected)

    def test_deserialize_collection(self):
        # arrange
        expected = TEST_LIST_SERIALIZATION
        input_data = TEST_LIST_SERIALIZATION_JSON

        # act
        actual = self.__json_camel_to_snake_case_deserializer.deserialize(input_data)

        # assert
        self.assertEqual(actual, expected)

    def test_serialize_collection_empty(self):
        # arrange
        expected = TEST_LIST_SERIALIZATION_EMPTY
        input_data = TEST_LIST_SERIALIZATION_EMPTY_JSON

        # act
        actual = self.__json_camel_to_snake_case_deserializer.deserialize(input_data)

        # assert
        self.assertEqual(actual, expected)