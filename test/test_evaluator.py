from evaluator import Evaluator
from elements.fact import Fact
from context import Context
from elements.rule import RuleTemplate, SatisfiedRule
import logging

import unittest  # https://docs.python.org/3/library/unittest.html


class TestEvaluator(unittest.TestCase):

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

    def test_evaluate_and(self):
        context = Context()
        context.rule_templates = [
            RuleTemplate.parse_rule_template("rule:op1('val11') and op2('val21') => add:op3('val31')")
        ]
        context.set_facts([
            Fact.parse("op1('val11')"),
            Fact.parse("op2('val21')")
        ])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        self.assertEqual(set(bound_rules), {
            SatisfiedRule.parse_satisfied_rule("rule:op1('val11') and op2('val21') => add:op3('val31')")
        })

        context.rule_templates = [
            RuleTemplate.parse_rule_template("rule:op1(X) and op2(Y) => add:op3(X)")
        ]
        context.set_facts([
            Fact.parse("op1('val11')"), Fact.parse("op1('val12')"),
            Fact.parse("op2('val21')"), Fact.parse("op2('val22')")
        ])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        self.assertEqual(set(bound_rules), {
            SatisfiedRule.parse_satisfied_rule("rule:op1('val11') and op2('val21') => add:op3('val11')"),
            SatisfiedRule.parse_satisfied_rule("rule:op1('val12') and op2('val21') => add:op3('val12')"),
            SatisfiedRule.parse_satisfied_rule("rule:op1('val11') and op2('val22') => add:op3('val11')"),
            SatisfiedRule.parse_satisfied_rule("rule:op1('val12') and op2('val22') => add:op3('val12')")
        })

        context.rule_templates = [
            RuleTemplate.parse_rule_template("rule:op1(X) and op2(X,Y) => add:op3(X)")
        ]
        context.set_facts([
            Fact.parse("op1('val11')"), Fact.parse("op1('val12')"),
            Fact.parse("op2('val11', 'val21')")
        ])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        self.assertEqual(set(bound_rules), {
            SatisfiedRule.parse_satisfied_rule("rule:op1('val11') and op2('val11','val21') => add:op3('val11')"),
        })

        context.rule_templates = [
            RuleTemplate.parse_rule_template("rule:op1(X) and op2(X,Y) => add:op3(X)")
        ]
        context.set_facts([
            Fact.parse("op1('val11')"), Fact.parse("op1('val12')")
        ])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        self.assertEqual(set(bound_rules), set())

        context.rule_templates = [
            RuleTemplate.parse_rule_template( "rule:op1(X,'val12') and op1(X,Y) => add:op3(X)")
        ]
        context.set_facts([
            Fact.parse("op1('val11','val12')"), Fact.parse("op1('val13','val14')")
        ])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        self.assertEqual(set(bound_rules), {
            SatisfiedRule.parse_satisfied_rule("rule:op1('val11','val12') and op1('val11','val12') => add:op3('val11')"),
        })

        context.rule_templates = [
            RuleTemplate.parse_rule_template("rule:op1(X) and op2(Y) => add:op3(X)")
        ]
        context.set_facts([Fact.parse("op1('val11')")])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        self.assertEqual(set(bound_rules), set())

        context.rule_templates = [
            RuleTemplate.parse_rule_template( "rule:op1(X) and not_a_fact(Y) => add:op3(X)")
        ]
        context.set_facts([
            Fact.parse("op1('val11')")
        ])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        self.assertEqual(set(bound_rules), set())

    def test_evaluate_not(self):
        context = Context()
        context.rule_templates = [
            RuleTemplate.parse_rule_template("rule:op1(X) and not op2(Y) => add:op2(Y)")
        ]
        context.set_facts([
            Fact.parse("op1('val11')"),
            Fact.parse("op2('val21')")
        ])
        bound_rules = Evaluator(context).evaluate(context.rule_templates[0])
        # "op2(X)" is resolved to "op2('val21') which is True so "not op2(X)" will evaluate to False
        self.assertEqual(set(bound_rules), set())

        context.rule_templates = [
            RuleTemplate.parse_rule_template("rule:op1(X) and not op2(Y) => add:op2(Y)")
        ]
        context.set_facts([
            Fact.parse("op1('val11')")
        ])
        # There is no op2 fact so "op2(X)" evaluates to False, so "not op2(X)" evaluates to True
        # -> the RHS stays as "add:op2(X)" which raises an - expected - exception
        self.assertRaises(Exception, Evaluator(context).evaluate, context.rule_templates[0])

    def test(self):
        pass


if __name__ == "__main__":
    unittest.main()
