from action import Action
import logging

import unittest  # https://docs.python.org/3/library/unittest.html

from expression import LeftExpression, RightExpression
from fact import Fact
from predicate import Predicate
from functions_handler import auto_register_functions
from rule import RuleTemplate, BoundRule, SatisfiedRule

auto_register_functions('functions_root')


class TestParser(unittest.TestCase):

    # https://docs.python.org/3/library/unittest.html#unittest.TestCase.setUpClass
    # Yes, for unittests, logging needs to be configured here
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(filename='test_logs.log',
                            filemode="w",
                            level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')

    def setUp(self):
        pass

    def test_operand_parser(self):
        operand_str = "op()"
        self.assertEqual(Predicate.parse(operand_str).to_string(), operand_str)

        operand_str = "op('op1')"
        self.assertEqual(Predicate.parse(operand_str).to_string(), operand_str)

        operand_str = "op('op1)"
        self.assertRaises(Exception, Predicate.parse, operand_str)

        operand_str = "op(op1')"
        self.assertRaises(Exception, Predicate.parse, operand_str)

        # TODO: this should work even if there are spaces between the values
        operand_str = "op('op1','op2')"
        self.assertEqual(Predicate.parse(operand_str).to_string(), operand_str)

        operand_str = "op('op1','op2)"
        self.assertRaises(Exception, Predicate.parse, operand_str)

        operand_str = "op('op1',op2')"
        self.assertRaises(Exception, Predicate.parse, operand_str)

        operand_str = "op(X)"
        self.assertEqual(Predicate.parse(operand_str).to_string(), operand_str)

        operand_str = "op(X,Y)"
        self.assertEqual(Predicate.parse(operand_str).to_string(), operand_str)

        operand_str = "op('op1',X)"
        self.assertEqual(Predicate.parse(operand_str).to_string(), operand_str)

    def test_action_parser(self):
        action_str = "add:op()"
        self.assertEqual(Action.parse(action_str).to_string(), action_str)

        action_str = "unknown:op()"
        self.assertRaises(ValueError, Action.parse, action_str)

        action_str = "function:my_function()"
        self.assertEqual(Action.parse(action_str).to_string(), action_str)

        action_str = "function:unknown()"
        self.assertRaises(Exception, Action.parse, action_str)

    def test_fact_parser(self):
        fact_str = "fact()"
        self.assertEqual(Fact.parse(fact_str).to_string(), fact_str)

        fact_str = "fact('val1')"
        self.assertEqual(Fact.parse(fact_str).to_string(), fact_str)

        fact_str = "fact(X)"
        self.assertRaises(Exception, Fact.parse, fact_str)

    def test_left_expression_parser(self):
        left_str = "op1(X) and op2(Y) and X!=Y and not op3(X)"
        self.assertEqual(LeftExpression.parse(left_str).to_string(), left_str)

        left_str = "op1(X) or op2(Y)"
        self.assertRaises(Exception, LeftExpression.parse, left_str)

    def test_right_expression_parser(self):
        pass

    def test_rule_template_parser(self):
        rule_str = "rule: op1(X) and op2(Y) => add:op3(X)"
        self.assertEqual(RuleTemplate.parse_rule_template(rule_str).to_string(), rule_str)

        rule_str = "rule: op1(X) and op1(X,Y) => add:op3(X)"
        self.assertRaises(Exception, RuleTemplate.parse_rule_template, rule_str)

        rule_str = "rule: op1(X) and op2(Y) => add:op3(Z)"
        self.assertRaises(Exception, RuleTemplate.parse_rule_template, rule_str)

    def test_bound_rule_parser(self):
        pass

    def test_satisfied_rule_parser(self):
        rule_str = "rule: op1('foo') and op2(Y) => add:op3('foo')"
        self.assertEqual(SatisfiedRule.parse_satisfied_rule(rule_str).to_string(), rule_str)

        rule_str = "rule: op1(X) and op2(Y) => add:op3(X)"
        self.assertRaises(Exception, SatisfiedRule.parse_satisfied_rule, rule_str)

if __name__ == "__main__":
    unittest.main()
