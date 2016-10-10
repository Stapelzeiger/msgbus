#include <ch.h>
#include <hal.h>
#include <string.h>
#include <stdarg.h>
#include <chprintf.h>
#include "example.h"
#include <msgbus/typed_messagebus.h>
#include <msgbus/type_print.h>

#define SENDER

#ifdef SENDER
#define NAME "Alice"
#else
#define NAME "Bob"
#endif

typed_messagebus_t bus;

static void print_fn(void *arg, const char *fmt, ...)
{
    BaseSequentialStream *chp = (BaseSequentialStream *)arg;
    va_list ap;
    va_start(ap, fmt);
    chvprintf(chp, fmt, ap);
    va_end(ap);
}

static THD_WORKING_AREA(receiver_thread, 500);
static THD_FUNCTION(receiver_thread_main, arg)
{
    chprintf((BaseSequentialStream *)&SD1, "example thread\n");

    typed_messagebus_topic_t *topic;
    topic = typed_messagebus_find_topic_blocking(&bus, "/example");

    static example_t msg;
    while (true) {
        typed_messagebus_topic_wait(topic, &msg);
        print_fn(arg, "%s:\n", "/example");
        messagebus_print_type_indent(print_fn, arg, topic->type, &msg, 1);
        if (msg.data) {
            palSetPad(GPIOE, GPIOE_LED7_GREEN);
        } else {
            palClearPad(GPIOE, GPIOE_LED7_GREEN);
        }
        palTogglePad(GPIOE, GPIOE_LED6_GREEN);
    }
}

int main(void)
{
    halInit();
    chSysInit();

    sdStart(&SD1, NULL); // USART1
    palSetPadMode(GPIOA, 9, PAL_MODE_ALTERNATE(7)); // TX
    palSetPadMode(GPIOA, 10, PAL_MODE_ALTERNATE(7)); // RX

    chprintf((BaseSequentialStream *)&SD1, "boot\n");

    typed_messagebus_init(&bus);

    static example_t buffer;
    static typed_messagebus_topic_t example_topic;
    typed_messagebus_topic_init(&example_topic, &example_type, &buffer);
    typed_messagebus_advertise_topic(&bus, &example_topic, "/example");

    chThdCreateStatic(receiver_thread, sizeof(receiver_thread), NORMALPRIO+1, receiver_thread_main, &SD1);

    while (1) {
        static example_t msg;
        strlcpy(msg.name, NAME, sizeof(msg.name));
        if (palReadPad(GPIOA, GPIOA_BUTTON)) {
            msg.data = 1;
        } else {
            msg.data = 0;
        }
        palClearPad(GPIOE, GPIOE_LED10_RED);
        typed_messagebus_topic_publish(&example_topic, &msg);
        chThdSleepMilliseconds(100);
    }
}
