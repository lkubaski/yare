from typing import Optional
import logging
from elements.fact import Fact
from elements.rule import RuleTemplate

class Context:
    SECTION_RULES = "rules"
    SECTION_FACTS = "facts"
    SECTION_GOAL = "goal"

    def __init__(self):
        self.rule_templates: list[RuleTemplate] = []
        self._facts: set[Fact] = set()
        self._facts_by_name: dict[str:set[Fact]] = {}
        self.goal: Optional[Fact] = None

    @property  # getter
    def facts(self):
        return self._facts

    @property  # getter
    def facts_by_name(self):
        return self._facts_by_name

    def add_facts(self, facts: list[Fact]):
        self._facts.update(facts)
        for fact in facts:
            self.facts_by_name.setdefault(fact.name, []).append(fact)
            # After a bound rule like "not op1('foo')" is satisfied (which happens if there is NO op1('foo') fact),
            # it doesn't need to be evaluated again UNLESS that fact gets added.
            # -> if this happens, the satisfied rule needs to be "unsatisfied" so that it can get evaluated again
            # when that fact gets added again
            self.remove_satisfied_rules(fact)
        for rule_template in self.rule_templates:
            rule_template.set_evaluate(facts)

    def remove_facts(self, facts: list[Fact]):
        for fact in facts:
            if fact in self._facts:
                self._facts.remove(fact)  # key must exist
            facts_by_name = self.facts_by_name.get(fact.name)  # returns None if the key does not exist
            if facts_by_name:
                facts_by_name.remove(fact)
                if not facts_by_name:  # if the list is now empty
                    del self.facts_by_name[fact.name]
                # After a bound rule like "op1('foo')" is satisfied (which happens if there IS a op1('foo') fact),
                # it doesn't need to be evaluated again UNLESS that fact gets removed.
                # -> if this happens, the bound rule needs to be "unsatisfied" so that it can get evaluated again
                # if that fact gets added again
            self.remove_satisfied_rules(fact)
        for rule_template in self.rule_templates:
            rule_template.set_evaluate(facts)

    def set_facts(self, facts: list[Fact]):
        self._facts = set()
        self._facts_by_name = {}
        self.add_facts(facts)

    def remove_satisfied_rules(self, fact: Fact):
        """
        Loops through all the rule templates and removes all the satisfied rules whose LHS contains
        the input fact
        """
        logging.debug(f">> fact='{fact}'")
        for rule_template in self.rule_templates:
            # Find the satisfied rules whose LHS match the input fact...
            matching_satisfied_rules = {
                satisfied_rule
                for satisfied_rule in rule_template.satisfied_rules
                # the condition below applies to each element returned by the 'for' loop above
                if fact in satisfied_rule.left_expression.predicates
            }
            # ... and remove them
            rule_template.satisfied_rules -= matching_satisfied_rules
            logging.debug(
                f"<< removed nbSatisfiedRules='{len(matching_satisfied_rules)}' from rule_template='{rule_template.name}'")
        logging.debug("<<")

    @staticmethod
    def get_config(file_path: str) -> dict:
        """
        Loads a configuration file containing rules, facts and a goal into a dictionary.
        """
        logging.debug(f">>")
        config = {}
        found_sections: set[str] = set()
        current_section = None
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip empty lines or comments
                if line.startswith("[") and line.endswith("]"):
                    # Handle section headers like [RULES], [FACTS], or [GOAL]
                    current_section = line[1:-1]
                    found_sections.add(current_section)
                    config[current_section] = []
                    continue
                if current_section == Context.SECTION_RULES:
                    config[current_section].append(line)
                elif current_section == Context.SECTION_FACTS:
                    config[current_section].append(line)
                elif current_section == Context.SECTION_GOAL:
                    config[current_section] = line

        if found_sections != {Context.SECTION_RULES, Context.SECTION_FACTS, Context.SECTION_GOAL}:
            raise Exception(f"Incorrect config file format")
        if len(config[Context.SECTION_RULES]) == 0:
            raise Exception(f"Incorrect config file format: at least one rule is required")
        if len(config[Context.SECTION_FACTS]) == 0:
            raise Exception(f"Incorrect config file format: at least one fact is required")
        if not config[Context.SECTION_GOAL]:
            raise Exception(f"Incorrect config file format: goal is missing")
        logging.debug(f"<<")
        return config

    def load_from_file(self, file_path: str):
        logging.debug(f">>")
        config = self.get_config(file_path)

        self.rule_templates = []
        self._facts_by_name = {}
        for rule in config[Context.SECTION_RULES]:
            rule_template = RuleTemplate.parse_rule_template(rule)
            self.rule_templates.append(rule_template)
        for fact in config[Context.SECTION_FACTS]:
            fact = Fact.parse(fact)
            self.add_facts([fact])
        self.goal = Fact.parse(config[Context.SECTION_GOAL])
        logging.debug(f"<<")

    def __str__(self):
        return f"<{self.__name__} rule_templates='{self.rule_templates}' facts='{self._facts}' goal='{self.goal}'>"
