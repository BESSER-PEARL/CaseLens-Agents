from typing import Union

from ui.vars import *


class Instruction:

    def __init__(self, field: str, text: str):
        self.field: str = field
        self.text: str = text

    def to_str(self):
        if self.field:
            return f"[{self.field}] {self.text}"
        else:
            return self.text

    def to_json(self):
        return {
            FIELD: self.field,
            TEXT: self.text
        }


class Filter:

    def __init__(self, field: str, operator: str, value: str):
        self.field: str = field
        self.operator: str = operator
        self.value: str = value

    def to_str(self):
        return f'{self.field} {self.operator} {self.value}'

    def to_json(self):
        return {
            FIELD: self.field,
            OPERATOR: self.operator,
            VALUE: self.value
        }


class Request:

    def __init__(
            self,
            action: str = None,
            target_value: Union[str, int] = None,
            date_from: str = None,
            date_to: str = None,
            filters=None,
            instructions=None
    ):
        if instructions is None:
            instructions = []
        if filters is None:
            filters = []
        self.action: str = action
        self.target_value: Union[str, int] = target_value
        self.date_from: str = date_from
        self.date_to: str = date_to
        self.filters: list[Filter] = filters
        self.instructions: list[Instruction] = instructions

    def to_json(self):
        return {
            ACTION: self.action,
            TARGET_VALUE: self.target_value,
            DATE_FROM: self.date_from,
            DATE_TO: self.date_to,
            FILTERS: [filter.to_json() for filter in self.filters],
            INSTRUCTIONS: [instruction.to_json() for instruction in self.instructions]
        }
