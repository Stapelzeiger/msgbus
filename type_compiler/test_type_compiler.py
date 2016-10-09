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
        expect = [
            TypeDefinition(
                typename='simple',
                docstring=[],
                entries=[
                    TypeDefinition.Entry(
                        type='int32',
                        name='x',
                        docstring='')
                ]
            )
        ]
        self.assertEqual(list(t), expect)

    def test_parse_type_definition(self):
        lines = [
            '# multiline',
            '# comment',
            '',
            '# example docstring',
            'example:',
            '    int32 x # x docstring',
            '    float arr[10]',
            '    string(10) str'
        ]
        t = parse(iter(enumerate(lines)))
        expect = [
            CommentBlock([' multiline', ' comment']),
            WhitespaceBlock(1),
            TypeDefinition(
                typename='example',
                docstring='example docstring',
                entries=[
                    TypeDefinition.Entry(type='int32', name='x', docstring=' x docstring'),
                    TypeDefinition.Entry(type='float', name='arr', docstring=None, array_sz=10),
                    TypeDefinition.Entry(type='string(10)', name='str', docstring=None),
                ]
            )
        ]
        self.assertEqual(list(t), expect)


class TestCCodeGeneration(unittest.TestCase):

    def test_C_struct_entry(self):
        entry = TypeDefinition.Entry(type='int32', name='foo')
        self.assertEqual(['    int32_t foo;'], C_struct_entry(entry))

    def test_C_struct_entry_string(self):
        entry = TypeDefinition.Entry(type=('string', 10), name='foo')
        self.assertEqual(['    char foo[11];'], C_struct_entry(entry))

    def test_C_struct_entry_array(self):
        entry = TypeDefinition.Entry(type='int32', name='foo', array_sz=10)
        self.assertEqual(['    int32_t foo[10];'], C_struct_entry(entry))

    def test_C_struct_entry_dynamic_array(self):
        entry = TypeDefinition.Entry(type='int32', name='foo', array_sz=10, dynamic_array=True)
        self.assertEqual(['    int32_t foo[10];',
                          '    uint16_t foo_len;'], C_struct_entry(entry))

    def test_C_struct_entry_dynamic_array_of_strings(self):
        entry = TypeDefinition.Entry(type=('string', 10), name='args', array_sz=3, dynamic_array=True)
        self.assertEqual(['    char args[3][11];',
                          '    uint16_t args_len;'], C_struct_entry(entry))
