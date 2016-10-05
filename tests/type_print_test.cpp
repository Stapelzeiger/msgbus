#include <CppUTest/TestHarness.h>
#include "../type_definition.h"
#include "../type_print.h"

typedef struct simple_s {
    float x;
    int32_t y;
    char str[20+1];
} simple_t;

static messagebus_type_entry_t simple_entries[] = {
    {
        .name = "x",
        .is_base_type = 1,
        .is_array = 0,
        .is_dynamic_array = 0,
        .struct_offset = offsetof(simple_t, x),
        .base_type = MESSAGEBUS_TYPE_FLOAT32,
    },
    {
        .name = "y",
        .is_base_type = 1,
        .is_array = 0,
        .is_dynamic_array = 0,
        .struct_offset = offsetof(simple_t, y),
        .base_type = MESSAGEBUS_TYPE_INT32,
    },
    {
        .name = "str",
        .is_base_type = 1,
        .is_array = 0,
        .is_dynamic_array = 0,
        .struct_offset = offsetof(simple_t, str),
        .base_type = MESSAGEBUS_TYPE_STRING,
        .size=20+1
    }
};

static messagebus_type_definition_t simple_type = {
    .nb_elements = 3,
    .elements = simple_entries,
};

typedef struct nested_s {
    int32_t x;
    simple_t simple;
} nested_t;

static messagebus_type_entry_t nested_entries[] = {
    {
        .name = "x",
        .is_base_type = 1,
        .is_array = 0,
        .is_dynamic_array = 0,
        .struct_offset = offsetof(simple_t, x),
        .base_type = MESSAGEBUS_TYPE_INT32,
    },
    {
        .name = "simple",
        .is_base_type = 0,
        .is_array = 0,
        .is_dynamic_array = 0,
        .struct_offset = offsetof(nested_t, simple),
        .type = &simple_type
    }
};

static messagebus_type_definition_t nested_type = {
    .nb_elements = 2,
    .elements = nested_entries,
};

extern "C"
void print_fn(void *p, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    char **buf = (char **)p;
    int n = vsprintf(*buf, fmt, ap);
    if (n > 0) {
        *buf += n;
    }
    va_end(ap);
}

TEST_GROUP(TypePrintTestGroup)
{
    char buffer[1000];
    void *arg;

    void setup(void)
    {
        memset(buffer, 0, sizeof(buffer));
        arg = &buffer;
    }
};

TEST(TypePrintTestGroup, CanPrintInt32)
{
    bool ret;
    messagebus_type_entry_t entry = {
        .name = "int",
        .is_base_type = 1,
        .is_array = 0,
        .is_dynamic_array = 0,
        .base_type = MESSAGEBUS_TYPE_INT32,
        .struct_offset = 0,
    };
    int32_t object = 123;
    ret = messagebus_print_entry(print_fn, &arg, &entry, &object, 0);
    CHECK_TRUE(ret)
    STRCMP_EQUAL("int: 123\n", buffer);
}

TEST(TypePrintTestGroup, CanPrintFloat32)
{
    bool ret;
    messagebus_type_entry_t entry = {
        .name = "float",
        .is_base_type = 1,
        .is_array = 0,
        .is_dynamic_array = 0,
        .base_type = MESSAGEBUS_TYPE_FLOAT32,
        .struct_offset = 0,
    };
    float object = 2.5;
    ret = messagebus_print_entry(print_fn, &arg, &entry, &object, 0);
    CHECK_TRUE(ret)
    STRCMP_EQUAL("float: 2.500000\n", buffer);
}

TEST(TypePrintTestGroup, CanPrintString)
{
    bool ret;
    messagebus_type_entry_t entry = {
        .name = "string",
        .is_base_type = 1,
        .is_array = 0,
        .is_dynamic_array = 0,
        .base_type = MESSAGEBUS_TYPE_STRING,
        .struct_offset = 0,
        .size = 5,
    };
    const char object[] = "CVRA";
    ret = messagebus_print_entry(print_fn, &arg, &entry, &object, 0);
    CHECK_TRUE(ret)
    STRCMP_EQUAL("string: \"CVRA\"\n", buffer);
}

TEST(TypePrintTestGroup, CanPrintSimpleType)
{
    simple_t object = {.x = 1.5f, .y = 42, .str = "hello world!"};
    messagebus_print_type(print_fn, &arg, &simple_type, &object);
    STRCMP_EQUAL(
        "x: 1.500000\n"
        "y: 42\n"
        "str: \"hello world!\"\n",
        buffer);
}

TEST(TypePrintTestGroup, CanPrintNestedType)
{
    nested_t object = {.x = 42, .simple = {.x = 1.0f, .y = 123, .str = "foo"}};
    messagebus_print_type(print_fn, &arg, &nested_type, &object);
    STRCMP_EQUAL(
        "x: 42\n"
        "simple:\n"
        "    x: 1.000000\n"
        "    y: 123\n"
        "    str: \"foo\"\n",
        buffer);
}
