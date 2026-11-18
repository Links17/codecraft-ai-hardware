#ifndef CODECRAFT_DEVICE_AUTH_H
#define CODECRAFT_DEVICE_AUTH_H

#include <stddef.h>
#include <stdint.h>

/* "Device " + Base64(16 ASCII hex + ':' + 32 ASCII hex) + terminating NUL. */
#define CODECRAFT_AUTH_HEADER_SIZE 76u

static inline int codecraft_hex_string(const char *value, size_t length)
{
    size_t i;
    if (value == NULL) {
        return 0;
    }
    for (i = 0; i < length; ++i) {
        unsigned char c = (unsigned char)value[i];
        if (!((c >= '0' && c <= '9') || (c >= 'A' && c <= 'F') ||
              (c >= 'a' && c <= 'f'))) {
            return 0;
        }
    }
    return value[length] == '\0';
}

/*
 * Inputs must be NUL-terminated, and output must not overlap either input.
 * Returns 1 on success, 0 on invalid input or insufficient output capacity.
 * Produces a header VALUE, not "Authorization:" or a complete HTTP request.
 * Requires no heap, TLS library, SDK, or platform-specific storage code.
 */
static inline int codecraft_device_authorization(const char *eui,
                                                const char *device_key,
                                                char *output,
                                                size_t capacity)
{
    static const char alphabet[] =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    static const char prefix[] = "Device ";
    unsigned char plaintext[49];
    size_t i, position = 0;
    volatile unsigned char *wipe;

    if (output == NULL || capacity == 0) {
        return 0;
    }
    output[0] = '\0';
    if (capacity < CODECRAFT_AUTH_HEADER_SIZE ||
        !codecraft_hex_string(eui, 16) || !codecraft_hex_string(device_key, 32)) {
        return 0;
    }
    for (i = 0; i < 16; ++i) {
        plaintext[i] = (unsigned char)eui[i];
    }
    plaintext[16] = ':';
    for (i = 0; i < 32; ++i) {
        plaintext[17 + i] = (unsigned char)device_key[i];
    }
    for (i = 0; i < 7; ++i) {
        output[position++] = prefix[i];
    }
    for (i = 0; i < sizeof plaintext; i += 3) {
        uint32_t value = (uint32_t)plaintext[i] << 16;
        if (i + 1 < sizeof plaintext) {
            value |= (uint32_t)plaintext[i + 1] << 8;
        }
        if (i + 2 < sizeof plaintext) {
            value |= plaintext[i + 2];
        }
        output[position++] = alphabet[(value >> 18) & 63u];
        output[position++] = alphabet[(value >> 12) & 63u];
        output[position++] = i + 1 < sizeof plaintext ? alphabet[(value >> 6) & 63u] : '=';
        output[position++] = i + 2 < sizeof plaintext ? alphabet[value & 63u] : '=';
    }
    output[position] = '\0';
    wipe = plaintext;
    for (i = 0; i < sizeof plaintext; ++i) {
        wipe[i] = 0;
    }
    return 1;
}

#endif
