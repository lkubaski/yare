from elements.action import Action
from elements.predicate import Predicate
import re


class LeftExpression:
    """Represents the LHS of a rule """
    # [()] represents the extra parenthesis that could exist like "(op1(X) and op2(X))"
    PREDICATE_REGEXP = r"\w+\(['A-Za-z0-9_, ]+\)|and|not|or|[()]"
    UNSUPPORTED_OPERATORS = {'or'}
    SUPPORTED_OPERATORS = {'and', 'not', '(', ')'}

    def __init__(self,
                 left_expression: str,
                 left_predicates: list[Predicate]):
        # We need to store the original string expression since it will be used when calling eval():
        self.expression: str = left_expression
        # We use a list and not a set because of the way Evaluator._get_bound_rules is implemented
        self.predicates: list[Predicate] = left_predicates

    @classmethod
    def parse(cls, left_expression: str):
        # Check that all the operators are supported
        ############################################
        # "op1(X) and op2(Y)" -> matches=['op1(X)', 'and', 'op2(Y)']
        matches = re.findall(cls.PREDICATE_REGEXP, left_expression)
        if any(match in cls.UNSUPPORTED_OPERATORS for match in matches):
            raise Exception(f"Incorrect syntax for left_expression={left_expression} (unsupported operator)")
        left_predicates = [Predicate.parse(match) for match in matches if
                         match not in cls.SUPPORTED_OPERATORS]

        result = cls(left_expression, left_predicates)
        return result

    def get_variable_names(self) -> set[str]:
        variables = set()
        for predicate in self.predicates:
            variables.update(predicate.get_variable_names())
        return variables

    def to_string(self):
        return self.expression

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<{self.__class__.__name__} expression='{self.expression}'>"


class RightExpression:
    """Represents the RHS of a rule """

    def __init__(self,
                 right_expression: str,
                 right_actions: set[Action],
                 ):
        self.expression: str = right_expression
        self.actions: set[Action] = right_actions

    @classmethod
    def parse(cls, right_expression: str):
        # This regexp splits on "," but excludes the "," that are inside parenthesis
        # "add:op1(X,Y) , add:op2(X,Y)" -> ["add:op1(X,Y)", "add:op2(X,Y)"]
        right_expr_elements = re.split(r'\s*,\s*(?![^(]*\))', right_expression)
        right_actions = {Action.parse(element) for element in right_expr_elements}
        result = cls(right_expression, right_actions)
        return result

    def to_string(self):
        return self.expression

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<{self.__class__.__name__} expression='{self.expression}'>"
