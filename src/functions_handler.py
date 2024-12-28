import pkgutil
import importlib

function_registry = {}


def register_function():
    """
    This registers functions that have the @register_function() decorator.
    """
    def decorator(func):
        function_registry[func.__name__] = func
        return func
    return decorator


def evaluate_function(function_name, rule_name, *args):
    func = function_registry.get(function_name)
    if not func:
        raise Exception(f"Function '{function_name}' is not registered.")
    return func(rule_name, *args)


def auto_register_functions(package_name):
    """
    Automatically discover and import all modules in the given package.
    This triggers the registration of functions in those modules.
    """
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package_name}.{module_name}")