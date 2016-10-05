#include <string.h>
#include <stdbool.h>
#include "type_definition.h"
#include "type_print.h"

static void print_indentataion(void (*print_fn)(void *, const char *, ...), void *arg, unsigned int indent)
{
    unsigned int i;
    for (i = 0; i < indent; i++) {
        print_fn(arg, "    ");
    }
}

bool messagebus_print_base_type(void (*print_fn)(void *, const char *, ...), void *arg,
                                int type, const void *p)
{
    union {
        float f;
        int32_t i;
    } data;
    switch (type) {
        case MESSAGEBUS_TYPE_INT32:
            memcpy(&data.i, p, sizeof(int32_t));
            print_fn(arg, "%d", data.i);
            break;
        case MESSAGEBUS_TYPE_FLOAT32:
            memcpy(&data.f, p, sizeof(float));
            print_fn(arg, "%f", data.f);
            break;
        case MESSAGEBUS_TYPE_STRING:
            print_fn(arg, "\"%s\"", p);
            break;
        default :
            return false;
            break;
    };
    return true;
}

bool messagebus_print_entry(void (*print_fn)(void *, const char *, ...), void *arg,
                            const messagebus_type_entry_t *entry, const void *object,
                            unsigned int indent)
{
    print_indentataion(print_fn, arg, indent);
    if (entry->is_array || entry->is_dynamic_array) {
        print_fn(arg, "todo");
    } else {
        object = (char *)object + entry->struct_offset;
        if (entry->is_base_type) {
            print_fn(arg, "%s: ", entry->name);
            if (!messagebus_print_base_type(print_fn, arg, entry->base_type, object)) {
                return false;
            }
            print_fn(arg, "\n");
        } else {
            print_fn(arg, "%s:\n", entry->name);
            _messagebus_print_type(print_fn, arg, entry->type, object, indent+1);
        }
    }
    return true;
}

bool _messagebus_print_type(void (*print_fn)(void *, const char *, ...), void *arg,
                            const messagebus_type_definition_t *type, const void *object,
                            unsigned int indent)
{
    int i;
    for (i = 0; i < type->nb_elements; i++) {
        if (!messagebus_print_entry(print_fn, arg, &type->elements[i], object, indent)) {
            return false;
        }
    }
    return true;
}

bool messagebus_print_type(void (*print_fn)(void *, const char *, ...), void *arg,
                           const messagebus_type_definition_t *type, const void *object)
{
    return _messagebus_print_type(print_fn, arg, type, object, 0);
}
