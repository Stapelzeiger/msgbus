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

    def test_parse_minimal_type_definition(self):
        lines = [
            'simple:',
            '    int32 x'
        ]
        t = parse(iter(enumerate(lines)))
        expect = TypeDefinition(
            typename='simple',
            docstring=[],
            entries=[
                TypeDefinitionEntry(
                    type='int32',
                    name='x',
                    docstring='')
            ])
        self.assertEqual(next(t), expect)
