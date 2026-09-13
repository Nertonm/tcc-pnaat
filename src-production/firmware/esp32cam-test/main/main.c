#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_camera.h"
#include "esp_err.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

#define SENSOR_GPIO GPIO_NUM_13
#define UART_BAUD 921600
#define DEBOUNCE_US 50000
#define COOLDOWN_US 250000
#define FRAME_SIZE FRAMESIZE_VGA
#define JPEG_QUALITY 12
#define AP_SSID "ESP32CAM-TEST"
#define AP_CHANNEL 6

/* AI-Thinker ESP32-CAM / ESP32-CAM-MB pin map. */
#define CAM_PIN_PWDN 32
#define CAMERA_WAKE_MS 100
#define CAMERA_WARMUP_MS 30
#define SENSOR_ARM_SETTLE_MS 500
#define CAM_PIN_RESET -1
#define CAM_PIN_XCLK 0
#define CAM_PIN_SIOD 26
#define CAM_PIN_SIOC 27
#define CAM_PIN_D7 35
#define CAM_PIN_D6 34
#define CAM_PIN_D5 39
#define CAM_PIN_D4 36
#define CAM_PIN_D3 21
#define CAM_PIN_D2 19
#define CAM_PIN_D1 18
#define CAM_PIN_D0 5
#define CAM_PIN_VSYNC 25
#define CAM_PIN_HREF 23
#define CAM_PIN_PCLK 22

static const char *TAG = "esp32cam_test";
static QueueHandle_t trigger_queue;
static volatile uint32_t dropped_isr_events;
static bool camera_ready;
static bool sensor_armed;

typedef enum {
    TRIGGER_SOURCE_E18 = 0,
    TRIGGER_SOURCE_USB_COMMAND = 1,
} TriggerSource;

typedef struct {
    uint32_t tick;
    int64_t timestamp_us;
    TriggerSource source;
} TriggerEvent;

static esp_err_t root_handler(httpd_req_t *req);
static esp_err_t capture_handler(httpd_req_t *req);
static esp_err_t stream_handler(httpd_req_t *req);
static httpd_handle_t start_webserver(void);
static esp_err_t start_wifi_ap(void);

static const char *trigger_source_name(TriggerSource source) {
    return source == TRIGGER_SOURCE_E18 ? "e18_d80nk" : "usb_command";
}

static uint32_t crc32(const uint8_t *data, size_t length) {
    uint32_t crc = 0xffffffffu;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (unsigned bit = 0; bit < 8; ++bit) {
            crc = (crc >> 1) ^ (0xedb88320u & (-(int32_t)(crc & 1u)));
        }
    }
    return ~crc;
}

static size_t base64_encode(const uint8_t *src, size_t len, char *dst) {
    static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t out = 0;
    for (size_t i = 0; i < len; i += 3) {
        uint32_t block = (uint32_t)src[i] << 16;
        if (i + 1 < len) block |= (uint32_t)src[i + 1] << 8;
        if (i + 2 < len) block |= src[i + 2];
        dst[out++] = alphabet[(block >> 18) & 0x3f];
        dst[out++] = alphabet[(block >> 12) & 0x3f];
        dst[out++] = (i + 1 < len) ? alphabet[(block >> 6) & 0x3f] : '=';
        dst[out++] = (i + 2 < len) ? alphabet[block & 0x3f] : '=';
    }
    dst[out] = '\0';
    return out;
}

static void IRAM_ATTR sensor_isr(void *arg) {
    TriggerEvent event = {
        .tick = (uint32_t)xTaskGetTickCountFromISR(),
        .timestamp_us = esp_timer_get_time(),
        .source = TRIGGER_SOURCE_E18,
    };
    BaseType_t higher = pdFALSE;
    if (xQueueSendFromISR(trigger_queue, &event, &higher) != pdTRUE) {
        dropped_isr_events++;
    }
    if (higher) {
        portYIELD_FROM_ISR();
    }
}

static esp_err_t init_camera(void) {
    camera_config_t config = {
        .ledc_channel = LEDC_CHANNEL_0,
        .ledc_timer = LEDC_TIMER_0,
        .pin_d0 = CAM_PIN_D0,
        .pin_d1 = CAM_PIN_D1,
        .pin_d2 = CAM_PIN_D2,
        .pin_d3 = CAM_PIN_D3,
        .pin_d4 = CAM_PIN_D4,
        .pin_d5 = CAM_PIN_D5,
        .pin_d6 = CAM_PIN_D6,
        .pin_d7 = CAM_PIN_D7,
        .pin_xclk = CAM_PIN_XCLK,
        .pin_pclk = CAM_PIN_PCLK,
        .pin_vsync = CAM_PIN_VSYNC,
        .pin_href = CAM_PIN_HREF,
        .pin_sccb_sda = CAM_PIN_SIOD,
        .pin_sccb_scl = CAM_PIN_SIOC,
        .pin_pwdn = CAM_PIN_PWDN,
        .pin_reset = CAM_PIN_RESET,
        .xclk_freq_hz = 20000000,
        .pixel_format = PIXFORMAT_JPEG,
        .frame_size = FRAME_SIZE,
        .jpeg_quality = JPEG_QUALITY,
        .fb_count = 1,
        .fb_location = CAMERA_FB_IN_PSRAM,
        .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
    };
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "CAMERA_INIT_FAIL err=0x%x", err);
        return err;
    }
    sensor_t *sensor = esp_camera_sensor_get();
    if (sensor == NULL) {
        ESP_LOGE(TAG, "CAMERA_SENSOR_NULL");
        return ESP_FAIL;
    }
    sensor->set_exposure_ctrl(sensor, 1);
    sensor->set_gain_ctrl(sensor, 1);
    sensor->set_aec2(sensor, 1);
    sensor->set_whitebal(sensor, 1);
    sensor->set_awb_gain(sensor, 1);
    sensor->set_ae_level(sensor, 1);
    sensor->set_brightness(sensor, 1);
    sensor->set_contrast(sensor, 1);
    gpio_set_level(CAM_PIN_PWDN, 1);
    printf("CAMERA_CONTROLS auto_exposure=1 auto_gain=1 aec2=1 awb=1 ae_level=1 standby=1\n");
    printf("CAMERA_OK framesize=%d quality=%d psram_free=%u\n", FRAME_SIZE,
           JPEG_QUALITY, (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
    return ESP_OK;
}

static void send_frame(uint32_t event_id, int64_t trigger_us, TriggerSource source) {
    int64_t wake_start_us = esp_timer_get_time();
    gpio_set_level(CAM_PIN_PWDN, 0);
    vTaskDelay(pdMS_TO_TICKS(CAMERA_WAKE_MS));
    int64_t wake_end_us = esp_timer_get_time();
    camera_fb_t *stale = esp_camera_fb_get();
    if (stale != NULL) esp_camera_fb_return(stale);
    vTaskDelay(pdMS_TO_TICKS(CAMERA_WARMUP_MS));
    int64_t warmup_end_us = esp_timer_get_time();
    int64_t capture_start_us = warmup_end_us;
    camera_fb_t *fb = esp_camera_fb_get();
    int64_t capture_end_us = esp_timer_get_time();
    if (fb == NULL || fb->format != PIXFORMAT_JPEG || fb->len == 0) {
        printf("CAPTURE_FAIL event=%lu wake_us=%lld warmup_us=%lld capture_us=%lld\n", (unsigned long)event_id,
               (long long)(wake_end_us - wake_start_us),
               (long long)(warmup_end_us - wake_end_us),
               (long long)(capture_end_us - capture_start_us));
        if (fb != NULL) esp_camera_fb_return(fb);
        gpio_set_level(CAM_PIN_PWDN, 1);
        return;
    }
    uint32_t checksum = crc32(fb->buf, fb->len);
    printf("FRAME_BEGIN v=1 encoding=base64 source=%s event=%lu trigger_us=%lld len=%u crc32=%08lx wake_us=%lld warmup_us=%lld capture_us=%lld\n",
           trigger_source_name(source), (unsigned long)event_id, (long long)trigger_us, (unsigned)fb->len,
           (unsigned long)checksum, (long long)(wake_end_us - wake_start_us),
           (long long)(warmup_end_us - wake_end_us),
           (long long)(capture_end_us - capture_start_us));
    fflush(stdout);
    char encoded[65];
    unsigned sequence = 0;
    for (size_t offset = 0; offset < fb->len; offset += 48) {
        size_t chunk = fb->len - offset;
        if (chunk > 48) chunk = 48;
        base64_encode(fb->buf + offset, chunk, encoded);
        printf("FRAME_DATA event=%lu seq=%u data=%s\n", (unsigned long)event_id,
               sequence++, encoded);
        fflush(stdout);
    }
    uart_wait_tx_done(UART_NUM_0, pdMS_TO_TICKS(5000));
    int64_t finished_us = esp_timer_get_time();
    printf("FRAME_END event=%lu tx_us=%lld total_us=%lld\n", (unsigned long)event_id,
           (long long)(finished_us - capture_end_us),
           (long long)(finished_us - trigger_us));
    fflush(stdout);
    esp_camera_fb_return(fb);
    gpio_set_level(CAM_PIN_PWDN, 1);
}

static httpd_handle_t start_webserver(void) {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    httpd_handle_t server = NULL;
    if (httpd_start(&server, &config) != ESP_OK) return NULL;

    static const httpd_uri_t root = {
        .uri = "/", .method = HTTP_GET, .handler = root_handler, .user_ctx = NULL
    };
    static const httpd_uri_t capture = {
        .uri = "/capture", .method = HTTP_GET, .handler = capture_handler, .user_ctx = NULL
    };
    static const httpd_uri_t stream = {
        .uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = NULL
    };
    httpd_register_uri_handler(server, &root);
    httpd_register_uri_handler(server, &capture);
    httpd_register_uri_handler(server, &stream);
    return server;
}

static esp_err_t root_handler(httpd_req_t *req) {
    static const char page[] =
        "<!doctype html><meta name=viewport content='width=device-width'>"
        "<title>ESP32-CAM</title><h1>ESP32-CAM</h1>"
        "<p><a href='/capture'>Foto unica</a></p>"
        "<img src='/stream' style='max-width:100%;height:auto'>";
    httpd_resp_set_type(req, "text/html; charset=utf-8");
    return httpd_resp_send(req, page, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t capture_handler(httpd_req_t *req) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb || fb->format != PIXFORMAT_JPEG) {
        if (fb) esp_camera_fb_return(fb);
        httpd_resp_send_err(req, HTTPD_500_INTERNAL_SERVER_ERROR, "capture failed");
        return ESP_FAIL;
    }
    httpd_resp_set_type(req, "image/jpeg");
    esp_err_t err = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return err;
}

static esp_err_t stream_handler(httpd_req_t *req) {
    static const char *content_type = "multipart/x-mixed-replace;boundary=frame";
    static const char *boundary = "\r\n--frame\r\n";
    char part[96];
    httpd_resp_set_type(req, content_type);
    while (true) {
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb || fb->format != PIXFORMAT_JPEG) {
            if (fb) esp_camera_fb_return(fb);
            break;
        }
        int part_len = snprintf(part, sizeof(part),
                                "%sContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
                                boundary, (unsigned)fb->len);
        esp_err_t err = httpd_resp_send_chunk(req, part, part_len);
        if (err == ESP_OK) err = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
        esp_camera_fb_return(fb);
        if (err != ESP_OK) break;
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    httpd_resp_send_chunk(req, NULL, 0);
    return ESP_OK;
}

static esp_err_t start_wifi_ap(void) {
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        return err;
    }
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_ap();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    wifi_config_t ap = {0};
    strncpy((char *)ap.ap.ssid, AP_SSID, sizeof(ap.ap.ssid));
    ap.ap.ssid_len = strlen(AP_SSID);
    ap.ap.channel = AP_CHANNEL;
    ap.ap.max_connection = 2;
    ap.ap.authmode = WIFI_AUTH_OPEN;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap));
    ESP_ERROR_CHECK(esp_wifi_start());
    return ESP_OK;
}

static void enqueue_synthetic_trigger(void) {
    TriggerEvent event = {
        .tick = (uint32_t)xTaskGetTickCount(),
        .timestamp_us = esp_timer_get_time(),
        .source = TRIGGER_SOURCE_USB_COMMAND,
    };
    if (xQueueSend(trigger_queue, &event, 0) != pdTRUE) {
        dropped_isr_events++;
    }
}

static void serial_rx_task(void *arg) {
    char command[32];
    size_t command_len = 0;
    while (true) {
        uint8_t byte;
        if (uart_read_bytes(UART_NUM_0, &byte, 1, pdMS_TO_TICKS(100)) != 1) continue;
        if (byte == '\n' || byte == '\r') {
            command[command_len] = '\0';
            if (strcmp(command, "CMD_CAPTURE") == 0) {
                enqueue_synthetic_trigger();
                printf("COMMAND_CAPTURE_ACCEPTED\n");
            } else if (command_len > 0) {
                printf("COMMAND_UNKNOWN name=%s\n", command);
            }
            command_len = 0;
        } else if (command_len < sizeof(command) - 1) {
            command[command_len++] = (char)byte;
        } else {
            command_len = 0;
            printf("COMMAND_FAIL reason=too_long\n");
        }
    }
}

static void capture_task(void *arg) {
    TriggerEvent event;
    int64_t last_trigger_us = 0;
    uint32_t event_id = 0;
    while (true) {
        if (xQueueReceive(trigger_queue, &event, portMAX_DELAY) != pdTRUE) continue;
        int64_t now = event.timestamp_us;
        if (now - last_trigger_us < DEBOUNCE_US) {
            printf("TRIGGER_SUPPRESSED reason=debounce\n");
            continue;
        }
        if (now - last_trigger_us < COOLDOWN_US) {
            printf("TRIGGER_SUPPRESSED reason=cooldown\n");
            continue;
        }
        last_trigger_us = now;
        event_id++;
        printf("TRIGGER_ACCEPTED source=%s event=%lu level=%d trigger_us=%lld dropped=%lu\n",
               trigger_source_name(event.source), (unsigned long)event_id,
               gpio_get_level(SENSOR_GPIO), (long long)now,
               (unsigned long)dropped_isr_events);
        if (camera_ready) send_frame(event_id, now, event.source);
    }
}

void app_main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    uart_set_baudrate(UART_NUM_0, UART_BAUD);
    esp_err_t uart_driver_err = uart_driver_install(UART_NUM_0, 2048, 0, 0, NULL, 0);
    if (uart_driver_err != ESP_OK && uart_driver_err != ESP_ERR_INVALID_STATE) {
        printf("UART_RX_FAIL err=0x%x\\n", uart_driver_err);
    }
    trigger_queue = xQueueCreate(8, sizeof(TriggerEvent));
    if (trigger_queue == NULL) {
        printf("FATAL queue_alloc\n");
        return;
    }
    gpio_config_t io = {
        .pin_bit_mask = 1ULL << SENSOR_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_NEGEDGE,
    };
    ESP_ERROR_CHECK(gpio_config(&io));
    gpio_config_t test_output = {
        .pin_bit_mask = 1ULL << GPIO_NUM_4,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&test_output));
    gpio_set_level(GPIO_NUM_4, 0);
    ESP_ERROR_CHECK(gpio_install_isr_service(ESP_INTR_FLAG_IRAM));

    printf("BOOT_TEST firmware=esp32cam_test sensor_gpio=%d active=LOW baud=%d\n",
           SENSOR_GPIO, UART_BAUD);
    printf("PSRAM free=%u\n", (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
    camera_ready = (init_camera() == ESP_OK);
    if (!camera_ready) {
        printf("READY sensor=1 camera=0\n");
    } else {
        printf("READY sensor=1 camera=1\n");
        printf("WEB_DISABLED transport=usb_serial\n");
        printf("CAPTURE_MODE on_demand=1 command=CMD_CAPTURE\n");
    }

    if (camera_ready) {
        vTaskDelay(pdMS_TO_TICKS(SENSOR_ARM_SETTLE_MS));
        int level = gpio_get_level(SENSOR_GPIO);
        if (level == 1) {
            ESP_ERROR_CHECK(gpio_isr_handler_add(SENSOR_GPIO, sensor_isr, NULL));
            sensor_armed = true;
            printf("SENSOR_ARMED level=1 settle_ms=%d\n", SENSOR_ARM_SETTLE_MS);
        } else {
            printf("SENSOR_NOT_ARMED level=%d reason=not_at_rest\n", level);
        }
    }

    BaseType_t rx_task_ok = xTaskCreatePinnedToCore(serial_rx_task, "serial_rx", 4096, NULL, 5, NULL, 0);
    BaseType_t capture_task_ok = xTaskCreatePinnedToCore(capture_task, "capture", 8192, NULL, 6, NULL, 1);
    if (rx_task_ok != pdPASS || capture_task_ok != pdPASS) {
        printf("TASKS_FAIL serial_rx=%d capture=%d\n", rx_task_ok, capture_task_ok);
        return;
    }
    printf("TASKS_READY serial_rx=core0 capture=core1 gpio4=LOW irq_queue=1 armed=%d\n", sensor_armed);
    vTaskDelete(NULL);
}
