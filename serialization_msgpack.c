#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "cmp/cmp.h"

#include "type_definition.h"


bool messagebus_cmp_ser_type(const void *var,
                             const messagebus_type_definition_t *type,
                             cmp_ctx_t *ctx);
bool messagebus_cmp_ser_struct_entry(const void *var,
                                     const messagebus_type_entry_t *entry,
                                     cmp_ctx_t *ctx);
bool messagebus_cmp_ser_value(const void *var,
                              const messagebus_type_entry_t *entry,
                              cmp_ctx_t *ctx);
bool messagebus_cmp_ser_value_once(const void *var,
                                   const messagebus_type_entry_t *entry,
                                   cmp_ctx_t *ctx);



bool messagebus_cmp_ser_value_once(const void *var,
                                   const messagebus_type_entry_t *entry,
                                   cmp_ctx_t *ctx)
{
    const void *var_entry = var + entry->struct_offset;
    if (entry->is_base_type) {
        switch (entry->base_type) {
        case MESSAGEBUS_TYPE_FLOAT32:
            return cmp_write_float(ctx, *(float*)var_entry);
        case MESSAGEBUS_TYPE_INT32:
            return cmp_write_int(ctx, *(int32_t*)var_entry);
        default:
            return false;
        }
    } else {
        return messagebus_cmp_ser_type(var_entry, entry->type, ctx);
    }
}


bool messagebus_cmp_ser_value(const void *var,
                              const messagebus_type_entry_t *entry,
                              cmp_ctx_t *ctx)
{
    if (entry->is_array || entry->is_dynamic_array) {
        return false; // todo arrays are not supported yet
    } else {
        return messagebus_cmp_ser_value_once(var, entry, ctx);
    }
}


bool messagebus_cmp_ser_struct_entry(const void *var,
                                     const messagebus_type_entry_t *entry,
                                     cmp_ctx_t *ctx)
{
    if (!cmp_write_str(ctx, entry->name, strlen(entry->name))) {
        return false;
    }
    return messagebus_cmp_ser_value(var, entry, ctx);
}


bool messagebus_cmp_ser_type(const void *var,
                             const messagebus_type_definition_t *type,
                             cmp_ctx_t *ctx)
{
    if (!cmp_write_map(ctx, type->nb_elements)) {
        return false;
    }
    int i;
    for (i = 0; i < type->nb_elements; i++) {
        if (!messagebus_cmp_ser_struct_entry(var, &type->elements[i], ctx)) {
            return false;
        }
    }
    return true;
}
