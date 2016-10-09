from collections import namedtuple

WhitespaceBlock = namedtuple('WhitespaceBlock', ['nb_lines'])
CommentBlock = namedtuple('CommentBlock', ['comments'])


class TypeDefinition():
    def __init__(self, typename, entries, docstring=''):
        self.typename = typename
        self.entries = entries
        self.docstring = docstring

    class Entry():
        def __init__(self, type, name, docstring='', array_sz=None, dynamic_array=False, str_len=0):
            self.type = type
            self.name = name
            self.docstring = docstring
            self.array_sz = array_sz
            self.dynamic_array = dynamic_array
            self.str_len = str_len

        def __eq__(self, other):  # used for unittests
            return self.__dict__ == other.__dict__

        def __repr__(self):
            return str(self.__dict__)

    def __eq__(self, other):  # used for unittests
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)


def split_line_in_expression_and_comment(line):
    expr_and_comment = line.split('#', 1)
    expr = expr_and_comment[0].split()
    if len(expr_and_comment) > 1:
        comment = expr_and_comment[1].rstrip()
    else:
        comment = ''
    return (expr, comment)


def is_type_definition(expr):
    return len(expr) == 1 and expr[0].endswith(':')


def parse(numbered_lines):
    line_idx, line = next(numbered_lines)
    expr, comment = split_line_in_expression_and_comment(line)
    while True:
        comments = []
        whitespace_lines = 0
        while not expr:
            if comment and whitespace_lines > 0:
                yield WhitespaceBlock(whitespace_lines)
                whitespace_lines = 0
            if not comment and comments:
                yield CommentBlock(comments)
                comments = []
            if comment:
                comments.append(comment)
            else:
                whitespace_lines += 1
            try:
                line_idx, line = next(numbered_lines)
            except StopIteration:
                if whitespace_lines > 0:
                    yield WhitespaceBlock(whitespace_lines)
                if comments:
                    yield CommentBlock(comments)
                raise StopIteration
            expr, comment = split_line_in_expression_and_comment(line)

        if whitespace_lines > 0:
            yield WhitespaceBlock(whitespace_lines)

        if is_type_definition(expr):
            if comment:
                comments.append(comment)
            name = expr[0].rstrip(':')
            entries = []
            while True:
                try:
                    line_idx, line = next(numbered_lines)
                except StopIteration:
                    yield TypeDefinition(name, entries, comments)
                    raise StopIteration
                expr, comment = split_line_in_expression_and_comment(line)
                if len(expr) == 2 and ':' not in expr[0]:
                    etype = expr[0]
                    str_len = 0
                    if etype.startswith('string('):
                        str_len = int(etype.strip('string()'))
                        etype = 'string'
                    varname = expr[1]
                    array_sz = None
                    dynamic_array = False
                    if varname.endswith(']'):
                        varname, arraylen_str = varname.split('[')
                        array_sz = int(arraylen_str.strip('<=]'))
                        if arraylen_str.startswith('<'):
                            dynamic_array = True
                            if not arraylen_str.startswith('<='):
                                array_sz -= 1

                    entries.append(TypeDefinition.Entry(etype, varname, comment, array_sz, dynamic_array, str_len))
                else:
                    yield TypeDefinition(name, entries, comments)
                    break
        else:
            raise Exception("line {}: unknown expression {}".format(line_idx+1, expr))


def parse_file(file):
    return list(parse(enumerate(file)))


def generate_C_comment_block(comments, doxygen=False):
    out = []
    if doxygen:
        start = '/**'
        indent = ' * '
    else:
        start = '/*'
        indent = ' *'
    out.append(start + comments[0])
    out += [indent + c for c in comments[1:]]
    if len(out) > 1:
        out.append(' */')
    else:
        out[0] += ' */'
    return out

C_types_map = {
    'int32': 'int32_t',
    'float32': 'float'
}

base_types_map = {
    'int32': 'MESSAGEBUS_TYPE_INT32',
    'float32': 'MESSAGEBUS_TYPE_FLOAT32',
    'string': 'MESSAGEBUS_TYPE_STRING'
}


def C_struct_entry(entry):
    ctype_char_array = ''
    if entry.type in C_types_map:
        ctype = C_types_map[entry.type]
    elif entry.type == 'string':
        ctype = 'char'
        ctype_char_array = '[{}]'.format(entry.str_len+1)
    else:  # custom type
        ctype = entry.type + '_t'
    array = ''
    if entry.array_sz is not None:
        array = '[{}]'.format(entry.array_sz)
    doc = ''
    if entry.docstring:
        doc = '  /**<{} */'.format(entry.docstring)
    else:
        doc = ''
    out = ['    {} {}{}{};{}'.format(ctype, entry.name, array, ctype_char_array, doc)]
    if entry.dynamic_array:
        out += ['    uint16_t {}_len;'.format(entry.name)]
    return out


def generate_C_struct_definition(typedef):
    out = []
    if typedef.docstring:
        out += generate_C_comment_block(typedef.docstring, doxygen=True)
    out.append('typedef struct {')
    for e in typedef.entries:
        out += C_struct_entry(e)
    out.append('}} {}_t;'.format(typedef.typename))
    return out


def generate_C_type_definition_header(typedef):
    return ['extern const messagebus_type_definition_t {}_type;'.format(typedef.typename)]


def generate_C_header(filename, elements):
    out = []
    out.append('/* THIS FILE IS AUTOMATICALLY GENERATED */')
    headerguard = filename.upper() + '_H'
    out.append('#ifndef ' + headerguard)
    out.append('#define ' + headerguard)
    out.append('')
    out.append('#include <stdint.h>')
    out.append('#include <msgbus/type_definition.h>')
    out.append('')
    for e in elements:
        if type(e) is CommentBlock:
            out += generate_C_comment_block(e.comments)
        if type(e) is WhitespaceBlock:
            out += [''] * e.nb_lines
        if type(e) is TypeDefinition:
            out += generate_C_struct_definition(e)

    out.append('')
    out.append('/* messagebus type definitions */')
    typedefs = [e for e in elements if type(e) is TypeDefinition]
    for t in typedefs:
        out += generate_C_type_definition_header(t)
    out.append('')
    out.append('#endif /* ' + headerguard + ' */')

    return '\n'.join(out)


def generate_C_type_definition_entry(typename, entry):
    out = []
    out.append('    {')
    out.append('        .name = "{}",'.format(entry.name))
    out.append('        .is_base_type = {},'.format(int(entry.type in base_types_map)))
    out.append('        .is_array = {},'.format(int(entry.array_sz is not None and not entry.dynamic_array)))
    out.append('        .is_dynamic_array = {},'.format(int(entry.dynamic_array)))
    if entry.array_sz:
        out.append('        .array_len = {},'.format(entry.array_sz))
    else:
        out.append('        .array_len = 0,')
    if entry.dynamic_array:
        out.append('        .dynamic_array_len_struct_offset = offsetof({}_t, {}_len),'.format(typename, entry.name))
    else:
        out.append('        .dynamic_array_len_struct_offset = 0,')
    out.append('        .struct_offset = offestof({}_t, {}),'.format(typename, entry.name))
    if entry.type in base_types_map:
        out.append('        .base_type = {},'.format(base_types_map[entry.type]))
        if entry.type is 'string':
            out.append('        .size = sizeof(char[{}]),'.format(entry.str_len+1))
        else:
            out.append('        .size = sizeof({}),'.format(C_types_map[entry.type]))
    else:
        out.append('        .type = &{}_type,'.format(entry.type))
        out.append('        .size = sizeof({}_t),'.format(entry.type))
    out.append('    },')
    return out


def generate_C_type_definition_entries(typedef):
    out = []
    out.append('static const messagebus_entry_t {}_entries[] = {{'.format(typedef.typename))
    for e in typedef.entries:
        out += generate_C_type_definition_entry(typedef.typename, e)
    out.append('};')
    return out


def generate_C_type_definition_object(typedef):
    out = []
    out.append('const messagebus_type_definition_t {}_type = {{'.format(typedef.typename))
    out.append('    .nb_elements = {},'.format(len(typedef.entries)))
    out.append('    .elements = {}_entries,'.format(typedef.typename))
    out.append('    .struct_size = sizeof({}_t),'.format(typedef.typename))
    out.append('};')
    return out


def generate_C_source(filename, elements):
    out = []
    out.append('/* THIS FILE IS AUTOMATICALLY GENERATED */')
    out.append('#include <msgbus/type_definition.h>')
    out.append('#include "{}.h"'.format(filename))
    out.append('')
    for e in elements:
        if type(e) is TypeDefinition:
            out += generate_C_type_definition_entries(e)
            out.append('')
            out += generate_C_type_definition_object(e)
            out.append('')

    return '\n'.join(out)

if __name__ == '__main__':
    f = open('example.type')
    t = parse_file(f)
    print(generate_C_header('example', t))
    print(generate_C_source('example', t))
