import unittest
from type_compiler import *


class TestParser(unittest.TestCase):

    def test_line_split(self):
        line = 'hello world # comment    \n'
        expr, comment = split_line_in_expression_and_comment(line)
        self.assertEqual(['hello', 'world'], expr)
        self.assertEqual(' comment', comment)

    def test_line_split_empty(self):
        line = '\n'
        expr, comment = split_line_in_expression_and_comment(line)
        self.assertEqual([], expr)
        self.assertEqual('', comment)
