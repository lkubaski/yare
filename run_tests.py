import sys
import os
import unittest

# IMPORTANT: modifying sys.path needs to be done before importing any custom module
sys.path.append(f"{os.getcwd()}/src")
sys.path.append(f"{os.getcwd()}/src/elements")
sys.path.append(f"{os.getcwd()}/test")

from test_engine import TestEngine
from test_parser import TestParser
from test_evaluator import TestEvaluator

# From https://stackoverflow.com/questions/15971735/running-a-single-test-from-unittest-testcase-via-the-command-line

def runs_one_test(test_name: str):
    suite = unittest.TestSuite()
    suite.addTest(TestEvaluator(test_name))
    runner = unittest.TextTestRunner()
    runner.run(suite)


def runs_all_tests(cls):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(cls)
    runner = unittest.TextTestRunner()
    runner.run(suite)


#runs_one_test("test")
runs_all_tests(TestParser)
runs_all_tests(TestEvaluator)
runs_all_tests(TestEngine)
