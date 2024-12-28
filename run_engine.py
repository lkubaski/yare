import sys
import os
import logging

# IMPORTANT: modifying sys.path needs to be done before importing any custom module
sys.path.append(f"{os.getcwd()}/src")
sys.path.append(f"{os.getcwd()}/src/elements")

from context import Context
from engine import RuleEngine
from functions_handler import auto_register_functions

# Important: the folder mentioned here must NOT be marked as a source directory in Intellij
auto_register_functions('functions_root')

# https://docs.python.org/3/library/logging.html#logging.basicConfig
# https://docs.python.org/3/library/logging.html#logrecord-attributes
logging.basicConfig(filename='logs.log',
                    filemode="w",
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')
log = f"Beginning of processing"
logging.info(log)
print(log)
context = Context()
context.load_from_file("./config/family.ini")
engine = RuleEngine(context)
log = f"\nEnd of processing: result for goal={context.goal} is {engine.run()}"
logging.info(log)
print(log)
