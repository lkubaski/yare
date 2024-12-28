#
# All the functions invoked in the rules (using "function:[FUNCTION_NAME]") have to be defined in this file
# and annotated with @register_function()

# The module that invokes the rule engine then needs to "import context_functions"

from functions_handler import register_function

@register_function()
def my_function(rule_name, *args):
    print(f"my_function called by rule={rule_name} with args={args}")

