from abc import ABC, abstractmethod
from typing import Union


class Instruction(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def to_json(self):
        pass


class SemanticInstruction(Instruction):

    def __init__(self, field: str, text: str):
        super().__init__()
        self.field: str = field
        self.text: str = text

    def to_str(self):
        if self.field:
            return f"[{self.field}] {self.text}"
        else:
            return self.text

    def to_json(self):
        return {
            'field': self.field,
            'text': self.text
        }


class FilterInstruction(Instruction):

    def __init__(self, field: str, operator: str, value: str):
        super().__init__()
        self.field: str = field
        self.operator: str = operator
        self.value: str = value

    def to_str(self):
        return f'{self.field} {self.operator} {self.value}'

    def to_json(self):
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value
        }


class Request:

    def __init__(self, action: str = None, target_value: Union[str, int] = None, date_from: str = None, date_to: str = None, instructions: list[Instruction] = None):
        if instructions is None:
            self.filters = []
            self.semantic_instructions = []
        else:
            self.set_instructions(instructions)
        self.action: str = action
        self.target_value: Union[str, int] = target_value
        self.date_from: str = date_from
        self.date_to: str = date_to

    def set_instructions(self, instructions: list[Instruction]):
        self.filters: list[FilterInstruction] = [instruction for instruction in instructions if isinstance(instruction, FilterInstruction)]
        self.semantic_instructions: list[SemanticInstruction] = [instruction for instruction in instructions if isinstance(instruction, SemanticInstruction)]

    def to_json(self):
        return {
            'action': self.action,
            'target_value': self.target_value,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'filters': [filter.to_json() for filter in self.filters],
            'semantic_instructions': [instruction.to_json() for instruction in self.semantic_instructions]
        }
