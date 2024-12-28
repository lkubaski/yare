from typing import cast

from elements.action import ActionType
from evaluator import Evaluator
from context import Context
from functions_handler import evaluate_function

from elements.fact import Fact
import logging

from elements.rule import RuleTemplate


class RuleEngine:
    #
    # Forward Chaining Inference Engine
    #
    def __init__(self, context: Context):
        self.context = context

    def run(self) -> bool:
        logging.debug(">>")
        has_new_facts = True
        found_goal = False
        while has_new_facts:
            logging.debug(f"Scanning through {len(self.context.rule_templates)} rules.")
            # has_new_facts, found_goal = self.process_rules()
            has_new_facts = self._process_rule_templates()
        if self.context.goal in self.context.facts:
            found_goal = True
        logging.debug(f"<< found_goal={found_goal}")
        return found_goal

    def _process_rule_templates(self) -> bool:
        logging.debug(f">> processing nb rules='{len(self.context.rule_templates)}'")
        has_new_facts = False
        for rule_template in self.context.rule_templates:
            has_new_facts = self._process_rule_template(rule_template)
            if has_new_facts:
                # The current rule_template has generated new facts, so we start looping on the rules
                # in order to go back to the main loop... which will start looping on all the rules again
                # (but from the beginning)
                break
        logging.debug(f"<< has_new_facts='{has_new_facts}'")
        return has_new_facts

    def _process_rule_template(self, rule_template: RuleTemplate) -> bool:
        logging.debug(f">> rule_template='{rule_template.name}'")
        has_new_facts = False
        new_satisfied_rules = Evaluator(self.context).evaluate(rule_template)
        for new_satisfied_rule in new_satisfied_rules:
            for action in new_satisfied_rule.right_expression.actions:
                if action.action_type == ActionType.ADD:
                    fact = Fact.parse(action.predicate.to_string())
                    if fact not in self.context.facts:
                        logging.debug(f"adding fact='{fact}'")
                        self.context.add_facts([fact])
                        has_new_facts = True
                elif action.action_type == ActionType.REMOVE:
                    fact: Fact = cast(Fact, action.predicate)
                    if fact in self.context.facts:
                        logging.debug(f"removing fact='{fact}'")
                        self.context.remove_facts([fact])
                        has_new_facts = True
                elif action.action_type == ActionType.FUNCTION:
                    # "*" takes an iterable and unpacks its elements so that they are passed as separate arguments to the function.
                    evaluate_function(action.predicate.name, rule_template.name, *action.predicate.values)
        rule_template.satisfied_rules.update(new_satisfied_rules)
        logging.debug(f"<< has_new_facts='{has_new_facts}'")
        return has_new_facts
