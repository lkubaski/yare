import re


class Predicate:
    CONSTANT_EXPRESSION = r"^'.*'$"  # begins AND ends with a "'"
    VARIABLE_EXPRESSION = r"^[^']*$"  # does not contain a "'"

    def __init__(self, name: str, values: list[str]):
        self.name: str = name
        self.values: list[str] = values

    @classmethod
    def parse(cls, predicate: str):
        # examples: "op1('value1')" or "op1('value1', 'value2')" or "op1()"
        elts = predicate.strip().split("(")
        name, values_str = elts[0].strip(), elts[1].strip()
        values = []
        if values_str != ')':  # no parameter: for example op1()
            values = values_str.split(",")
            values = [value.replace(")", "").strip() for value in values]
            for value in values:
                if not (cls.is_constant(value) or cls.is_variable(value)):
                    raise Exception(f"Invalid predicate={predicate} (one of the values is not a constant nor a variable)")
        result = cls(name, values)
        return result

    def get_variable_names(self) -> set[str]:
        return {value for value in self.values if Predicate.is_variable(value)}

    @staticmethod
    def is_constant(value: str) -> bool:
        return re.match(Predicate.CONSTANT_EXPRESSION, value) is not None

    @staticmethod
    def is_variable(value: str) -> bool:
        return re.match(Predicate.VARIABLE_EXPRESSION, value) is not None

    def to_string(self):
        return f"{self.name}({','.join(self.values)})"

    def __eq__(self, other):
        if isinstance(other, Predicate):
            result = self.name == other.name and self.values == other.values
            return result
        return False

    def __hash__(self):
        result = hash((self.name, tuple(self.values)))
        return result

    def __str__(self):
        return f"<{self.__class__.__name__} predicate='{self.to_string()}'>"
