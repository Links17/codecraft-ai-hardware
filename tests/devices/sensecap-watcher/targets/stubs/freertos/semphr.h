/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include "idf_bsp_stub.h"
#include <pthread.h>
typedef unsigned TickType_t;
typedef pthread_mutex_t *SemaphoreHandle_t;
#define pdTRUE 1
SemaphoreHandle_t xSemaphoreCreateMutex(void);
int xSemaphoreTake(SemaphoreHandle_t mutex, TickType_t timeout);
void xSemaphoreGive(SemaphoreHandle_t mutex);
void vSemaphoreDelete(SemaphoreHandle_t mutex);
