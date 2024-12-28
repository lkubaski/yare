from enum import Enum

from elements.predicate import Predicate
from functions_handler import function_registry


class ActionType(Enum):
    ADD = "add"
    REMOVE = "remove"
    FUNCTION = "function"


class Action:

    def __init__(self, predicate: Predicate, action_type: ActionType):
        self.predicate = predicate
        self.action_type = action_type

    @classmethod
    def parse(cls, action: str):
        parts = action.split(":", 1)
        if len(parts) != 2:
            raise Exception(f"Incorrect syntax for action={action} (missing ':' separator)")
        predicate = Predicate.parse(parts[1].strip())
        action_type = ActionType(parts[0].strip())
        if action_type == ActionType.FUNCTION:
            function = function_registry.get(predicate.name)
            if not function:
                raise Exception(f"Function '{predicate.name}' is not registered.")
        return Action(predicate, action_type)

    def to_string(self):
        return f"{self.action_type.value}:{self.predicate.to_string()}"

    def __eq__(self, other):
        if isinstance(other, Action):
            return self.predicate == other.predicate and self.action_type == other.action_type
        return False

    def __str__(self):
        return f"<{self.__class__.__name__} predicate='{self.predicate.to_string()}' action_type='{self.action_type}'>"

    def __hash__(self):
        return hash((self.predicate, self.action_type))

    def __repr__(self):
        return self.__str__()
