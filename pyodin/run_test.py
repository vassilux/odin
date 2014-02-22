#!/usr/bin/python

import sys
import os
'''
Helper to run all unit testSuite
Please create a new test file with the prefix test_ into file name
Module all_tests(test/all_tests.py) discover and run all test cases
'''
import unittest
import test.all_tests
testSuite = test.all_tests.create_test_suite()
text_runner = unittest.TextTestRunner().run(testSuite)

