import copy

from elements.fact import Fact
from engine import RuleEngine
from context import Context
from elements.rule import RuleTemplate
import logging

# https://docs.python.org/3/library/unittest.html
import unittest


class TestEngine(unittest.TestCase):
    # https://docs.python.org/3/library/unittest.html#unittest.TestCase.setUpClass
    # Yes, for unittests, logging needs to be configured here
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(filename='test_logs.log',
                            filemode="w",
                            level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')

    def test_single1(self):
        rule_templates = [
            RuleTemplate.parse_rule_template("rule1:op1(X) => add:op2(X)"),
            RuleTemplate.parse_rule_template("rule2:op3(X) => add:op1(X)"),
            RuleTemplate.parse_rule_template("rule3:op4(X) => add:op1(X)"),
            RuleTemplate.parse_rule_template("rule4:not op4('val52') => add:op3('val52')"),
        ]
        facts =[
            Fact.parse("op3('val3')"),
            Fact.parse("op4('val51')"),
        ]

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("op2('val3')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 9)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("op2('val52')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 9)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("does_not_exist('foo')")
        self.assertFalse(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 9)


    def test_single2(self):
        rule_templates = [
            RuleTemplate.parse_rule_template("rule1:op1(X) => add:op3(X)"),
            RuleTemplate.parse_rule_template("rule2:op2(X) => add:op3(X)"),
            RuleTemplate.parse_rule_template("rule3:op1(X) and op2(X) => add:op4(X)"),
        ]
        facts = [
            Fact.parse("op1('val11')"), Fact.parse("op1('val12')"),
            Fact.parse("op2('val21')"), Fact.parse("op2('val12')")
        ]

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("op3('val11')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 8)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("op4('val12')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 8)

    def test_single3(self):
        rule_templates = [
            RuleTemplate.parse_rule_template("rule1:type(X,'apple') => add:eatable(X)"),
            RuleTemplate.parse_rule_template("rule2:type(X,'banana') => add:eatable(X)"),
            RuleTemplate.parse_rule_template("rule3:apple(X) => add:type(X,'apple')"),
            RuleTemplate.parse_rule_template("rule4:banana(X) => add:type(X,'banana')"),
        ]
        facts = [
            Fact.parse("apple('golden')"),
            Fact.parse("banana('cavendish')"),
        ]

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("eatable('golden')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 6)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("eatable('cavendish')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 6)

    def test_multiple(self):
        context = Context()
        rule_templates = [
            RuleTemplate.parse_rule_template("rule1:man(A) and parent(A,B) => add:father(A,B)"),
            RuleTemplate.parse_rule_template("rule2:woman(A) and parent(A,B) => add:mother(A,B)"),
            RuleTemplate.parse_rule_template("rule3:man(A) and parent(B,A) => add:son(A,B)"),
            RuleTemplate.parse_rule_template("rule4:woman(A) and parent(B,A) => add:daughter(A,B)"),
            RuleTemplate.parse_rule_template("rule5:parent(A,B) and parent(A,C) and B!=C => add:siblings(B,C)"),
            RuleTemplate.parse_rule_template("rule6:parent(A,B) and parent(C,B) and A!=C => add:married(A,C)"),
            RuleTemplate.parse_rule_template("rule7:parent(A,B) and parent(B,C) and man(A) => add:grand_father(A,C)"),
            RuleTemplate.parse_rule_template("rule8:parent(A,B) and parent(B,C) and woman(A) => add:grand_mother(A,C)"),
            RuleTemplate.parse_rule_template("rule9:grand_father(A,B) => add:grand_parent(A,B)"),
            RuleTemplate.parse_rule_template("rule10:grand_mother(A,B) => add:grand_parent(A,B)"),
        ]
        facts = [
            Fact.parse("man('george')"), Fact.parse("man('larry')"), Fact.parse("man('peter')"),
            Fact.parse("woman('sophia')"), Fact.parse("woman('jacqueline')"), Fact.parse("woman('catherine')"),
            Fact.parse("parent('george','larry')"), Fact.parse("parent('george','sophia')"),
            Fact.parse("parent('jacqueline','larry')"), Fact.parse("parent('jacqueline','sophia')"),
            Fact.parse("parent('peter','jacqueline')"), Fact.parse("parent('catherine','jacqueline')")
        ]

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("mother('jacqueline','larry')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 45)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("son('larry','jacqueline')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 45)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("siblings('larry','sophia')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 45)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("married('jacqueline','george')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 45)

        context = Context()
        context.rule_templates = copy.deepcopy(rule_templates)
        context.set_facts(facts)
        context.goal = Fact.parse("grand_parent('catherine','larry')")
        self.assertTrue(RuleEngine(context).run())
        self.assertTrue(len(context.facts) == 45)


    def test(self):
        pass

if __name__ == "__main__":
    unittest.main()
