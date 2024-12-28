from elements.expression import LeftExpression
from elements.fact import Fact
from context import Context
from elements.predicate import Predicate
from elements.rule import RuleTemplate, BoundRule, SatisfiedRule
from itertools import product
import re
import logging


class Evaluator(dict):
    def __init__(self, context: Context):
        super().__init__()
        self.context = context

    def evaluate(self, rule_template: RuleTemplate) -> set[SatisfiedRule]:
        """
        Evaluates a rule and returns the list of new satisfied rules.
        (which is the list of the satisfied rules that were discovered AFTER the rule_template was evaluated.)

        Example:
        Rule = "op1(X) and op2(X) => op3(X)"
        Facts = [op1('foo'), ap1('bar'), op2('foo')]
        Results = ["op1('foo') and op2('foo") => op3('foo')"]

        """
        logging.debug(f">> rule_template={rule_template.name}")
        satisfied_rules: set[SatisfiedRule] = set()
        if not rule_template.evaluate:
            logging.debug(f"<< skipping evaluation for rule template='{rule_template.name}'")
            return satisfied_rules

        bound_rules = Evaluator._get_bound_rules(rule_template, self.context.facts)
        for bound_rule in bound_rules:
            if any(bound_rule.rule == satisfied_rule.rule for satisfied_rule in rule_template.satisfied_rules):
                logging.debug(f"Skipping evaluation for bound rule '{bound_rule}' (already satisfied)")
                continue
            is_satisfied = self._evaluate_bound_rule(bound_rule)
            if is_satisfied:
                satisfied_rule = SatisfiedRule.parse_satisfied_rule(bound_rule.rule)
                satisfied_rules.add(satisfied_rule)
        rule_template.evaluate = False
        logging.debug(f"<< returning nb satisfied rules='{len(satisfied_rules)}' for rule='{rule_template.name}'")
        return satisfied_rules

    def _evaluate_bound_rule(self, bound_rule: BoundRule) -> bool:
        """
        Evaluates (via python eval()) the LHS of a bound rule and returns the result of the evaluation

        Note that an expression containing variables may still evaluate to 'True'.
        For example: "not op1(X)" evaluates to 'True' is there is no op1 fact
        """
        logging.debug(f">> bound_rule={bound_rule}")
        # Invoking eval() with an expression that contains variables requires using a dict as the second eval() parameter
        # where the dict keys are the variable names and the dict values are the variable values
        # (in this case the dict we use is the current object itself)
        for left_predicate in bound_rule.left_expression.predicates:
            self.update({value: value for value in left_predicate.values if Predicate.is_variable(value)})
        # Note: calling eval() will invoke self.__missing__()
        result = eval(bound_rule.left_expression.expression, self)
        logging.debug(f"<< evaluation result={result}")
        return result

    @staticmethod
    def _get_bound_rules(rule_template: RuleTemplate, facts: set[Fact]) -> list[BoundRule]:
        """
        Returns the list of all the bound rules for the given rule template and the given facts
        """
        logging.debug(f">> rule_template={rule_template}")
        bound_rules: list[BoundRule] = []

        left_bound_expressions = Evaluator._get_left_bound_expressions(rule_template.left_expression, facts)

        # { op1(A):{0:A}, op2(B,A):{0:B, 1:A}, op3(B):{0:B} }
        predicates_position_variable = Evaluator._get_predicates_position_variable(rule_template.left_expression)
        for left_bound_expr in left_bound_expressions:
            variables_values_dict = Evaluator._get_variables_values_dict(left_bound_expr,
                                                                         rule_template.left_expression,
                                                                         predicates_position_variable,
                                                                         )
            # OK so when "op1(A) and op2(B,A) and op3(B)" gets bounded:
            # - A should get replaced with the SAME value in op1 and op2
            # - B should get replaced with the SAME value in op1 and op3
            # So if the bound expression contains multiple values for A, we know that it's not a valid expression
            is_valid = all(len(variables_values_dict[variable]) <= 1 for variable in variables_values_dict)
            if is_valid:
                bound_right_expr = Evaluator._get_bound_right_expression(rule_template.right_expression.expression,
                                                                         variables_values_dict)
                bound_rule_str = f"{rule_template.name}:{left_bound_expr.expression} => {bound_right_expr}"
                bound_rule = BoundRule.parse_rule_template(bound_rule_str)
                bound_rules.append(bound_rule)
        logging.debug(f"<< returning nb bound rules={len(bound_rules)}")
        return bound_rules

    @staticmethod
    def _get_variables_values_dict(left_bound_expr: LeftExpression,
                                   left_unbound_expr: LeftExpression,
                                   predicate_position_variable: dict[Predicate: dict[int:list]],
                                   ) -> dict[str:set]:
        """
        Returns a dict where:
        - the keys are the variable names that were used to resolve the bound left expression
        - the values are the resolved values

        example:
        - bound_left_expr = "op1(X) and op2(X,Y)
        - unbound_left_expr = "op1('x1') and op2('x2', 'y1")
        - result = { X : {'x1','x2}, Y : {'y1'}}
        """
        variables_values_dict = {variable: set() for variable in left_unbound_expr.get_variable_names()}
        for bound_predicate_index, bound_predicate in enumerate(left_bound_expr.predicates):
            for bound_value_index, bound_value in enumerate(bound_predicate.values):
                if Predicate.is_variable(bound_value):
                    # The LHS of a bound rule may contain variables
                    # For example when the parent rule template contains "op1(X)" and when there is no op1(X) fact
                    continue
                # get the original name of the variable from the not-bounded predicate:
                template_predicate = left_unbound_expr.predicates[bound_predicate_index]
                # check of the bound_value_index was originally a variable in the rule_template
                # This may not be the case if the rule template contains an predicate like op1('foo')
                # since in that case, 'foo' is already bound (so to speak)
                if bound_value_index in predicate_position_variable[template_predicate]:
                    variable = predicate_position_variable[template_predicate][bound_value_index]
                    variables_values_dict[variable].add(bound_value)
        return variables_values_dict

    @staticmethod
    def _get_left_bound_expressions(left_expression: LeftExpression, facts: set[Fact]) -> list[LeftExpression]:
        """
        From a rule template, generate all the bound rules that match the given facts.

        If one of the input predicates from the rule doesn't match any fact, it's left "as is".
        -> so for example if the rule template contains "op1(X") and if there is no op1 fact, then
        all the generated bound rules will contain "op1(X)".
        """
        bound_expressions: list[LeftExpression] = []

        left_predicates_facts = Evaluator._get_predicates_matching_facts(left_expression.predicates, facts)
        fact_combos = list(product(*(left_predicates_facts.values())))
        for fact_combo in fact_combos:
            bound_left_expr = str(left_expression.expression)
            left_predicate_and_fact_list = list(zip(left_predicates_facts.keys(), fact_combo))
            for left_predicate, fact in left_predicate_and_fact_list:
                # Replaces a left predicate with a known fact
                bound_left_expr = bound_left_expr.replace(left_predicate.to_string(), fact.to_string())
                pass
            bound_expressions.append(LeftExpression.parse(bound_left_expr))
        return bound_expressions

    @staticmethod
    def _get_bound_right_expression(right_expression: str, variable_mapping: dict[str, set[str]]) -> str:
        """
        Returns a string where the input expression variables have been replaced by their value
        expression = "op2(X)"
        mapping = { X : 123 }
        result = "op2(123)"
        """

        def process_parentheses(match) -> str:
            parenthesis_content = match.group(1)
            replaced_content = replace_parenthesis_content(parenthesis_content)
            return f"({replaced_content})"

        def replace_parenthesis_content(content: str) -> str:
            parts = re.split(r",\s*", content)  # split around ","
            replaced_parts = []
            for part in parts:
                if re.match(r"^'.*'$", part):
                    # single quoted strings are left as is
                    replaced_parts.append(part)
                else:
                    # this code below retrieves the first element from a set
                    if (part in variable_mapping) and (len(variable_mapping[part]) == 1):
                        value = next(iter(variable_mapping[part]))
                        part = part.replace(part, value)
                    replaced_parts.append(part)
            return ", ".join(replaced_parts)

        parentheses_pattern = r"\(([^()]+)\)"
        bound_expression = re.sub(parentheses_pattern, process_parentheses, right_expression)
        return bound_expression

    @staticmethod
    def _get_predicates_position_variable(left_unbound_expr: LeftExpression) -> dict[Predicate: dict[int:str]]:
        """
        Returns a dict where a key is a left predicates and a value is a dict of { variable_name_index: variable_name } pair
        Example:
        - input = op1(A) and op2(B,A) and op3(B, 'foo')
        - output = { op1(A):{0:A}, op2(B,A):{0:B, 1:A}, op3(B):{0:B} }
        """
        result: dict[Predicate: dict[int:str]] = {}
        for predicate in left_unbound_expr.predicates:
            if predicate not in result:
                result[predicate] = {}
            for index, value in enumerate(predicate.values):
                if Predicate.is_variable(value):
                    result[predicate].update({index: value})
        return result

    @staticmethod
    def _get_predicates_matching_facts(predicates: list[Predicate], facts: set[Fact]) -> dict[Predicate:set[Fact]]:
        """
        Returns the list of facts that match each input predicate
        The return value is a dict where:
        - the keys are the predicates
        - the values are the matching facts for each predicate
        If an predicate does NOT have any matching facts, that predicate is NOT added to the dict.
        """
        result: dict[Predicate:set[Fact]] = {}
        for next_predicate in predicates:
            if next_predicate not in result:
                matching_facts = Evaluator._get_predicate_matching_facts(next_predicate, facts)
                if matching_facts:  # no key with empty values
                    result[next_predicate] = matching_facts
        return result

    @staticmethod
    def _get_predicate_matching_facts(predicate: Predicate, facts: set[Fact]) -> set[Fact]:
        """
        Returns the facts that match an predicate
        (the predicate values may be constants or variables like for example "op1(X, 'foo')" )

        Input predicate = op1(X, 'b')
               Facts = op1('a', 'b') & op1('c', 'b') & op1('c', 'd') & op2('a', 'b')
              Result = op1('a', 'b') & op1('c', 'b')
       """
        matches: set[Fact] = set()
        # for next_fact in self.context.facts:
        for next_fact in facts:
            if next_fact.name != predicate.name:
                continue
            match = True
            for next_fact_index, next_fact_value in enumerate(next_fact.values):
                next_predicate_value = predicate.values[next_fact_index]
                if Predicate.is_constant(next_predicate_value) and not next_predicate_value == next_fact_value:
                    # A variable match everything, a constant match another constant that has the same value
                    # -> the only scenario where there is NO match is when comparing a constant with a different constant
                    match = False
                    break
            if match:
                matches.add(next_fact)
        return matches

    def __missing__(self, key: str):
        """
        invoked via self["missing_function"]("arg")
        OR via eval("missing_function(arg)")
        """

        def method(*args: tuple, **kwargs) -> bool:
            facts = self.context.facts_by_name.get(key, [])
            result = False
            if facts:
                # Note that we convert the second argument to a "list" because args is a "tuple"
                values = [f"'{arg}'" for arg in args]
                fact = Fact(key, values)
                result = fact in facts
            #logging.debug(f">> << key={key}, args={args} -> result={result}")
            return result

        return method