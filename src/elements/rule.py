from elements.action import ActionType
from elements.expression import LeftExpression, RightExpression
from elements.fact import Fact
from elements.predicate import Predicate


class RuleTemplate:

    def __init__(self, rule: str, name: str, left_expression: LeftExpression, right_expression: RightExpression):
        self.rule: str = rule
        self.name: str = name

        self.left_expression = left_expression
        self.right_expression = right_expression
        # A "satisfied rule" is a BoundRule whose LHS evaluates to "true"
        self.satisfied_rules: set[BoundRule] = set()
        # Needs to be set to "True" when a fact used on the RHS is added/removed from the knowledge base
        self.evaluate: bool = False

    @classmethod
    def parse_rule_template(cls, rule: str):
        # Check that there is the ':' separator
        ########################################
        parts = rule.split(":", 1)
        if len(parts) != 2:
            raise Exception(f"Incorrect syntax for rule={rule} (missing ':')")
        name = parts[0].strip()
        # Check that there is the '=>' separator
        ########################################
        parts = parts[1].split("=>")
        if len(parts) != 2:
            raise Exception(f"Incorrect syntax for rule={rule} (missing '=>')")
        left_expression = LeftExpression.parse(parts[0].strip())
        right_expression = RightExpression.parse(parts[1].strip())
        # check that all the predicates from the same type have the same number of values
        ##################################################################
        all_predicates = left_expression.predicates + [right_action.predicate for right_action in
                                                       right_expression.actions]
        predicate_values = {}
        for predicate in all_predicates:
            if predicate.name not in predicate_values:
                predicate_values[predicate.name] = len(predicate.values)
            else:
                if predicate_values[predicate.name] != len(predicate.values):
                    raise Exception(f"Incorrect syntax for rule={rule} (the same predicate has different values)")

        # Check that all the variables on the RHS are used on the LHS
        #############################################################
        unused_variables = cls.get_unused_right_variables(left_expression, right_expression)
        if unused_variables:
            raise Exception(
                f"Incorrect syntax for rule='{rule}' (unused right variables: {', '.join(unused_variables)})"
            )

        result = cls(rule, name, left_expression, right_expression)
        return result

    @classmethod
    def get_unused_right_variables(cls, left_expression: LeftExpression, right_expression: RightExpression) -> set[str]:
        # Gets the list of RHS variables that are not used on the LHS
        # In that case, this means that the rule is invalid
        # For example "op1(X) -> op2(Y)" is invalid because Y is not used on the LHS
        left_variables = set()
        for left_predicate in left_expression.predicates:
            for variable in left_predicate.values:
                if Predicate.is_variable(variable):
                    left_variables.add(variable)
        right_predicates = {action.predicate for action in right_expression.actions}
        right_variables = set()
        for right_predicate in right_predicates:
            for variable in right_predicate.values:
                if Predicate.is_variable(variable):
                    right_variables.add(variable)
        unused_variables = right_variables - left_variables
        return unused_variables

    def set_evaluate(self, facts: list[Fact]):
        """
        sets the value of self.evaluate by checking if any of the input fact names are referenced on the LHS
        """
        for fact in facts:
            is_fact_name_used = any(fact.name == predicate.name for predicate in self.left_expression.predicates)
            if is_fact_name_used and not self.evaluate:
                self.evaluate = True
                break

    def to_string(self):
        return self.rule

    def __eq__(self, other):
        if isinstance(other, RuleTemplate):
            return self.rule == other.rule
        return False

    def __hash__(self):
        return hash(self.rule)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<{self.__class__.__name__} rule='{self.rule}'>"


class BoundRule(RuleTemplate):
    """
    A bound Rule, where the variables have been replaced with the bound values using the known facts
    -> a BoundRule may contain variables on the LHS and could still be evaluated
    (for example "not op1(X)" evaluates to true if there is no op1 fact)
    """

    def __init__(self, rule: str, name: str, left_expression: LeftExpression, right_expression: RightExpression):
        super().__init__(rule, name, left_expression, right_expression)

    @classmethod
    def parse_bound_rule(cls, rule: str):
        rule_template: RuleTemplate = RuleTemplate.parse_rule_template(rule)
        result = cls(rule, rule_template.name, rule_template.left_expression, rule_template.right_expression)
        return result

    def __eq__(self, other):
        if isinstance(other, BoundRule):
            return self.rule == other.rule
        return False

    def __hash__(self):
        return hash(self.rule)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<{self.__class__.__name__} rule='{self.rule}'>"


class SatisfiedRule(BoundRule):
    """
    A satisfied rule is a bound rule:
    - whose LHS evaluates to True
    - whose RHS only contains facts (ie: there are no variables)
    """

    def __init__(self, rule: str, name: str, left_expression: LeftExpression, right_expression: RightExpression):
        super().__init__(rule, name, left_expression, right_expression)

    @classmethod
    def parse_satisfied_rule(cls, rule: str):
        bound_rule: BoundRule = BoundRule.parse_bound_rule(rule)
        result = cls(rule, bound_rule.name, bound_rule.left_expression, bound_rule.right_expression)
        # check that all the RHS actions are fully resolved
        for action in result.right_expression.actions:
            if action.action_type == ActionType.ADD or action.action_type == ActionType.REMOVE:
                # This will raise an exception if it's not an actual fact
                Fact.parse(action.predicate.to_string())
        return result

    def __eq__(self, other):
        if isinstance(other, SatisfiedRule):
            return self.rule == other.rule
        return False

    def __hash__(self):
        return hash(self.rule)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<{self.__class__.__name__}rule='{self.rule}'>"


if __name__ == '__main__':
    pass
