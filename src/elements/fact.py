from elements.predicate import Predicate


class Fact(Predicate):

    def __init__(self, name: str, values: list[str]):
        super().__init__(name, values)

    @classmethod
    def parse(cls, operand: str):
        fact = super().parse(operand)
        all_constants = all(cls.is_constant(value) for value in fact.values)
        if not all_constants:
            raise Exception(f"Invalid fact='{operand}' (variables are not allowed)")
        return fact
