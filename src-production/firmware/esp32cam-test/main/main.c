#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "driver/ledc.h"
#include "esp_rom_sys.h"
#include "esp_camera.h"
#include "esp_err.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_system.h"

#define SENSOR_GPIO GPIO_NUM_13
#define UART_BAUD 921600
#define DEBOUNCE_US 50000
#define COOLDOWN_US 250000
#define FRAME_SIZE FRAMESIZE_VGA
#define JPEG_QUALITY 12

/* AI-Thinker ESP32-CAM / ESP32-CAM-MB pin map. */
#define CAM_PIN_PWDN 32

/* Energia da camera.
 * CAM_PWDN_WIRED=1: medido - com pin_pwdn=-1 a inicializacao falha; com
 * GPIO32 o driver cicla 1->0 e o sensor responde. GPIO32 e o PWDN real.
 * CAM_POWER_GPIO>=0: GPIO que habilita o 3V3 da camera por chave de carga
 * (MOSFET/load-switch) para corte real de energia. -1 = sem chave: o que
 * existe e standby do sensor (PWDN alto + XCLK parado), nao corte de 3V3. */
#define CAM_PWDN_WIRED 1
#define CAM_POWER_GPIO -1
#define CAM_POWER_SETTLE_MS 60
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
static int camera_ativa = 0;
static int forcar_falha_init = 0;      /* diagnostico: proxima captura falha na init */            /* 1 = driver inicializado/energizado */
static int transport_bin = 0;          /* 0 = texto base64, 1 = binario enquadrado */
static uint32_t bin_chunks_total = 0;
static int uart_baud_atual = UART_BAUD;
#define UART_BAUD_MIN 9600
#define UART_BAUD_MAX 3000000

/* Estado de energia da camera.
 * camera_clock_off: o driver para o LEDC; aqui o pino XCLK volta a entrada com
 * pull-down para nao deixar clock residual no sensor. Retorna o erro do LEDC.
 * set_camera_power: liga/desliga o 3V3 da camera quando existe chave de carga.
 * Sem chave a camera permanece alimentada, e o log diz isso explicitamente em
 * vez de apresentar standby como desligamento. */
static esp_err_t camera_clock_off(void)
{
    esp_err_t err = ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
    gpio_config_t xclk_off = {
        .pin_bit_mask = 1ULL << CAM_PIN_XCLK,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&xclk_off);
    return err;
}

static void set_camera_power(int on)
{
#if CAM_POWER_GPIO >= 0
    gpio_set_level(CAM_POWER_GPIO, on ? 1 : 0);
    if (on) vTaskDelay(pdMS_TO_TICKS(CAM_POWER_SETTLE_MS));
#endif
    (void)on;
}

static int camera_power_is_on(void)
{
#if CAM_POWER_GPIO >= 0
    return gpio_get_level(CAM_POWER_GPIO);
#else
    return -1;
#endif
}

/* PWDN do sensor: 1 = power-down (standby), 0 = ativo. */
/* ---------------------------------------------------------------- log serializado
 * Duas tasks escrevem no UART0 (serial_rx_task no core 0 e capture_task no core 1).
 * Sem serializacao as linhas se fundem e, pior, um log pode cair DENTRO de uma
 * mensagem binaria e invalidar o frame por CRC. Todo o caminho de escrita passa
 * por este mutex. */
static SemaphoreHandle_t uart_mutex;

static void log_printf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    if (uart_mutex != NULL) xSemaphoreTake(uart_mutex, portMAX_DELAY);
    vprintf(fmt, ap);
    if (uart_mutex != NULL) xSemaphoreGive(uart_mutex);
    va_end(ap);
}

static inline void uart_write_msg(const uint8_t *buf, size_t len)
{
    if (uart_mutex != NULL) xSemaphoreTake(uart_mutex, portMAX_DELAY);
    uart_write_bytes(UART_NUM_0, (const char *)buf, len);
    if (uart_mutex != NULL) xSemaphoreGive(uart_mutex);
}

static void camera_pwdn_assert(int power_down)
{
#if CAM_PWDN_WIRED
    gpio_set_level(CAM_PIN_PWDN, power_down ? 1 : 0);
#else
    (void)power_down;
#endif
}





typedef enum {
    TRIGGER_SOURCE_E18 = 0,
    TRIGGER_SOURCE_USB_COMMAND = 1,
} TriggerSource;

typedef struct {
    uint32_t tick;
    int64_t timestamp_us;
    TriggerSource source;
} TriggerEvent;


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

static void camera_config_fill(camera_config_t *config, int pin_pwdn) {
    *config = (camera_config_t){
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
        .pin_pwdn = pin_pwdn,
        .pin_reset = CAM_PIN_RESET,
        .xclk_freq_hz = 20000000,
        .pixel_format = PIXFORMAT_JPEG,
        .frame_size = FRAME_SIZE,
        .jpeg_quality = JPEG_QUALITY,
        .fb_count = 1,
        .fb_location = CAMERA_FB_IN_PSRAM,
        .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
    };
}

/* Detecta o sensor com o PWDN sob controle manual do firmware: o driver recebe
 * pin_pwdn=-1 para nao ciclar a linha, entao o nivel que colocamos e o que vale.
 * Retorna 1 se o sensor respondeu (camera operante). */
static int camera_detect_with_pwdn(int pwdn_high)
{
    camera_config_t probe_cfg;
    camera_config_fill(&probe_cfg, -1);
    camera_pwdn_assert(pwdn_high);
    vTaskDelay(pdMS_TO_TICKS(30));
    if (esp_camera_init(&probe_cfg) != ESP_OK) {
        esp_camera_deinit();
        return 0;
    }
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb != NULL) esp_camera_fb_return(fb);
    esp_camera_deinit();
    return 1;
}

static esp_err_t init_camera(void) {
    camera_config_t config;
    camera_config_fill(&config, CAM_PWDN_WIRED ? CAM_PIN_PWDN : -1);
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "CAMERA_INIT_FAIL err=0x%x", err);
        return err;
    }
    sensor_t *sensor = esp_camera_sensor_get();
    if (sensor == NULL) {
        ESP_LOGE(TAG, "CAMERA_SENSOR_NULL");
        esp_camera_deinit();          /* nao deixar driver/clock vivos no erro */
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
    log_printf("CAMERA_CONTROLS auto_exposure=1 auto_gain=1 aec2=1 awb=1 ae_level=1 standby=1\n");
    log_printf("CAMERA_OK framesize=%d quality=%d psram_free=%u\n", FRAME_SIZE,
           JPEG_QUALITY, (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
    return ESP_OK;
}


/* Unico caminho de volta ao standby. Todo ramo que ligou a camera passa por
 * aqui: fim de captura, falha de init e fim do teste de energia. Deixar isso
 * espalhado ja causou camera energizada em caminho de erro. */
static void camera_standby(const char *motivo, uint32_t event_id)
{
    esp_err_t deinit_err = esp_camera_deinit();
    camera_ready = false;
    camera_ativa = 0;
    camera_pwdn_assert(1);
    esp_err_t clock_err = camera_clock_off();
    set_camera_power(0);
    log_printf("CAMERA_OFF event=%lu motivo=%s power_en=%d deinit=0x%x ledc_stop=0x%x\n",
               (unsigned long)event_id, motivo, camera_power_is_on(), deinit_err, clock_err);
}

/* ---------------------------------------------------------------- transporte binario
 * Contrato v1 (little-endian):
 *   SOF A5 5A | VER | TYPE | FLAGS | EVENT u16 | SEQ u32 | LEN u16 | CRC16(VER..LEN)
 *   + payload (LEN) + CRC32(payload)
 * TYPE: 1=BEGIN 2=CHUNK 3=END 4=ACK 5=NACK.
 * BEGIN leva 16 B (total_len u32, frame_crc32 u32, trigger_us i64) e END leva o
 * CRC do frame inteiro, para o host validar antes de publicar a imagem. */
#define BIN_TYPE_BEGIN 1
#define BIN_TYPE_CHUNK 2
#define BIN_TYPE_END   3
#define BIN_HDR_SIZE   15
#define BIN_CHUNK      1024

static uint8_t bin_buf[BIN_HDR_SIZE + BIN_CHUNK + 4];
static uint8_t bin_payload[BIN_CHUNK];

static uint16_t crc16_ccitt(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (int bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
        }
    }
    return crc;
}

static void put_u16(uint8_t *dst, uint16_t value)
{
    dst[0] = value & 0xFF;
    dst[1] = (value >> 8) & 0xFF;
}

static void put_u32(uint8_t *dst, uint32_t value)
{
    for (int i = 0; i < 4; ++i) dst[i] = (value >> (8 * i)) & 0xFF;
}

static void put_u64(uint8_t *dst, uint64_t value)
{
    for (int i = 0; i < 8; ++i) dst[i] = (value >> (8 * i)) & 0xFF;
}

static uint16_t bin_encode(uint8_t msg_type, uint16_t event_id, uint32_t seq,
                           const uint8_t *payload, uint16_t len)
{
    size_t n = 0;
    bin_buf[n++] = 0xA5;
    bin_buf[n++] = 0x5A;
    bin_buf[n++] = 1;                    /* VER */
    bin_buf[n++] = msg_type;
    bin_buf[n++] = 0;                    /* FLAGS */
    put_u16(bin_buf + n, event_id); n += 2;
    put_u32(bin_buf + n, seq); n += 4;
    put_u16(bin_buf + n, len); n += 2;
    put_u16(bin_buf + n, crc16_ccitt(bin_buf + 2, 11)); n += 2;
    if (len > 0) {
        memcpy(bin_buf + n, payload, len);
        n += len;
    }
    put_u32(bin_buf + n, crc32(payload, len)); n += 4;
    return (uint16_t)n;
}

static void send_frame_bin(uint32_t event_id, int64_t trigger_us, TriggerSource source,
                           camera_fb_t *fb, uint32_t frame_crc)
{
    log_printf("FRAME_INFO source=%s event=%lu trigger_us=%lld len=%u crc32=%08lx encoding=bin\n",
           trigger_source_name(source), (unsigned long)event_id, (long long)trigger_us,
           (unsigned)fb->len, (unsigned long)frame_crc);

    put_u32(bin_payload + 0, (uint32_t)fb->len);
    put_u32(bin_payload + 4, frame_crc);
    put_u64(bin_payload + 8, (uint64_t)trigger_us);
    uint16_t n = bin_encode(BIN_TYPE_BEGIN, (uint16_t)event_id, 0, bin_payload, 16);
    uart_write_msg(bin_buf, n);

    uint32_t seq = 0;
    for (size_t offset = 0; offset < fb->len; offset += BIN_CHUNK) {
        size_t chunk = fb->len - offset;
        if (chunk > BIN_CHUNK) chunk = BIN_CHUNK;
        n = bin_encode(BIN_TYPE_CHUNK, (uint16_t)event_id, seq++, fb->buf + offset, (uint16_t)chunk);
        uart_write_msg(bin_buf, n);
    }
    bin_chunks_total = seq;

    put_u32(bin_payload, frame_crc);
    n = bin_encode(BIN_TYPE_END, (uint16_t)event_id, 0, bin_payload, 4);
    uart_write_msg(bin_buf, n);
}

static void send_frame(uint32_t event_id, int64_t trigger_us, TriggerSource source) {
    int64_t wake_start_us = esp_timer_get_time();
    int64_t wake_end_us = esp_timer_get_time();
    /* Prime do sensor: consome o primeiro frame apos a inicializacao para o
     * AEC convergir. Removido uma vez e medido: o frame enviado sai escuro
     * (luma media 29 vs 84 com o prime), entao NAO e sobra. */
    camera_fb_t *prime = esp_camera_fb_get();
    if (prime != NULL) esp_camera_fb_return(prime);
    vTaskDelay(pdMS_TO_TICKS(CAMERA_WARMUP_MS));
    int64_t warmup_end_us = esp_timer_get_time();
    int64_t capture_start_us = warmup_end_us;
    camera_fb_t *fb = esp_camera_fb_get();
    int64_t capture_end_us = esp_timer_get_time();
    if (fb == NULL || fb->format != PIXFORMAT_JPEG || fb->len == 0) {
        log_printf("CAPTURE_FAIL event=%lu wake_us=%lld warmup_us=%lld capture_us=%lld\n", (unsigned long)event_id,
               (long long)(wake_end_us - wake_start_us),
               (long long)(warmup_end_us - wake_end_us),
               (long long)(capture_end_us - capture_start_us));
        if (fb != NULL) esp_camera_fb_return(fb);
        return;
    }
    uint32_t checksum = crc32(fb->buf, fb->len);
    if (transport_bin) {
        send_frame_bin(event_id, trigger_us, source, fb, checksum);
        uart_wait_tx_done(UART_NUM_0, pdMS_TO_TICKS(5000));
        int64_t bin_end_us = esp_timer_get_time();
        log_printf("FRAME_END_BIN event=%lu tx_us=%lld total_us=%lld chunks=%lu\n",
               (unsigned long)event_id, (long long)(bin_end_us - capture_end_us),
               (long long)(bin_end_us - trigger_us), (unsigned long)bin_chunks_total);
        fflush(stdout);
        esp_camera_fb_return(fb);
        return;
    }
    log_printf("FRAME_BEGIN v=1 encoding=base64 source=%s event=%lu trigger_us=%lld len=%u crc32=%08lx wake_us=%lld warmup_us=%lld capture_us=%lld\n",
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
        log_printf("FRAME_DATA event=%lu seq=%u data=%s\n", (unsigned long)event_id,
               sequence++, encoded);
        fflush(stdout);
    }
    uart_wait_tx_done(UART_NUM_0, pdMS_TO_TICKS(5000));
    int64_t finished_us = esp_timer_get_time();
    log_printf("FRAME_END event=%lu tx_us=%lld total_us=%lld\n", (unsigned long)event_id,
           (long long)(finished_us - capture_end_us),
           (long long)(finished_us - trigger_us));
    fflush(stdout);
    esp_camera_fb_return(fb);
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
                log_printf("COMMAND_CAPTURE_ACCEPTED\n");
            } else if (strncmp(command, "CMD_BAUD ", 9) == 0) {
                int novo = atoi(command + 9);
                if (novo < UART_BAUD_MIN || novo > UART_BAUD_MAX) {
                    log_printf("BAUD_ACK ok=0 pedido=%d motivo=fora_da_faixa\n", novo);
                } else {
                    log_printf("BAUD_ACK ok=1 de=%d para=%d\n", uart_baud_atual, novo);
                    fflush(stdout);
                    uart_wait_tx_done(UART_NUM_0, pdMS_TO_TICKS(2000));
                    vTaskDelay(pdMS_TO_TICKS(60));
                    uart_flush_input(UART_NUM_0);
                    uart_set_baudrate(UART_NUM_0, (uint32_t)novo);
                    uart_baud_atual = novo;
                    log_printf("BAUD_ATIVO %d\n", uart_baud_atual);
                    fflush(stdout);
                }
            } else if (strcmp(command, "CMD_TRANSPORT BIN") == 0) {
                transport_bin = 1;
                log_printf("TRANSPORT mode=bin chunk=%d\n", BIN_CHUNK);
            } else if (strcmp(command, "CMD_TRANSPORT TEXT") == 0) {
                transport_bin = 0;
                log_printf("TRANSPORT mode=text\n");
            } else if (strcmp(command, "CMD_TEST_FALHA_INIT") == 0) {
                forcar_falha_init = 1;
                log_printf("TEST_FALHA_INIT armado=1\n");
            } else if (strcmp(command, "CMD_SENSOR") == 0) {
                set_camera_power(1);
                int detect_on = camera_detect_with_pwdn(0);
                camera_clock_off();
                log_printf("SENSOR_TEST pwdn=0 detect=%d\n", detect_on);
                int detect_off = camera_detect_with_pwdn(1);
                camera_clock_off();
                log_printf("SENSOR_TEST pwdn=1 detect=%d\n", detect_off);
                log_printf("SENSOR_VERDICT pwdn_desliga_sensor=%d\n",
                       (detect_on && !detect_off) ? 1 : 0);
                camera_standby("fim_do_teste", 0);
            } else if (strcmp(command, "CMD_STATUS") == 0) {
                log_printf("STATUS camera=%s driver=%d power_en=%d armed=%d transport=%s baud=%d\n",
                       camera_ativa ? "ativa" : "standby", camera_ready ? 1 : 0,
                       camera_power_is_on(), sensor_armed ? 1 : 0,
                       transport_bin ? "bin" : "text", uart_baud_atual);
            } else if (command_len > 0) {
                log_printf("COMMAND_UNKNOWN name=%s\n", command);
            }
            command_len = 0;
        } else if (command_len < sizeof(command) - 1) {
            command[command_len++] = (char)byte;
        } else {
            command_len = 0;
            log_printf("COMMAND_FAIL reason=too_long\n");
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
            log_printf("TRIGGER_SUPPRESSED reason=debounce\n");
            continue;
        }
        if (now - last_trigger_us < COOLDOWN_US) {
            log_printf("TRIGGER_SUPPRESSED reason=cooldown\n");
            continue;
        }
        last_trigger_us = now;
        event_id++;
        log_printf("TRIGGER_ACCEPTED source=%s event=%lu level=%d trigger_us=%lld dropped=%lu\n",
               trigger_source_name(event.source), (unsigned long)event_id,
               gpio_get_level(SENSOR_GPIO), (long long)now,
               (unsigned long)dropped_isr_events);
        set_camera_power(1);
        camera_pwdn_assert(0);
        vTaskDelay(pdMS_TO_TICKS(CAMERA_WAKE_MS));
        camera_ready = (!forcar_falha_init && init_camera() == ESP_OK);
        forcar_falha_init = 0;
        if (!camera_ready) {
            log_printf("CAPTURE_FAIL event=%lu reason=camera_init\n", (unsigned long)event_id);
            camera_standby("falha_init", event_id);
            continue;
        }
        camera_ativa = 1;
        send_frame(event_id, now, event.source);
        camera_standby("fim_da_captura", event_id);
    }
}

void app_main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    uart_mutex = xSemaphoreCreateMutex();
    uart_set_baudrate(UART_NUM_0, (uint32_t)uart_baud_atual);
    esp_err_t uart_driver_err = uart_driver_install(UART_NUM_0, 2048, 0, 0, NULL, 0);
    if (uart_driver_err != ESP_OK && uart_driver_err != ESP_ERR_INVALID_STATE) {
        log_printf("UART_RX_FAIL err=0x%x\\n", uart_driver_err);
    }
    trigger_queue = xQueueCreate(8, sizeof(TriggerEvent));
    if (trigger_queue == NULL) {
        log_printf("FATAL queue_alloc\n");
        return;
    }
#if CAM_POWER_GPIO >= 0
    gpio_config_t power_en = {
        .pin_bit_mask = 1ULL << CAM_POWER_GPIO,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&power_en));
#endif
#if CAM_PWDN_WIRED
    gpio_config_t pwdn_out = {
        .pin_bit_mask = 1ULL << CAM_PIN_PWDN,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&pwdn_out));
#endif
    camera_pwdn_assert(1);
    set_camera_power(0);
    camera_clock_off();
    log_printf("POWER_MODEL pwdn_wired=%d pwdn_pin=%d power_gpio=%d\n",
           CAM_PWDN_WIRED, CAM_PIN_PWDN, CAM_POWER_GPIO);
    log_printf("CAMERA_OFF boot=1 reason=await_irq power_en=%d\n", camera_power_is_on());
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

    log_printf("BOOT_TEST firmware=esp32cam_test sensor_gpio=%d active=LOW baud=%d\n",
           SENSOR_GPIO, uart_baud_atual);
    log_printf("PSRAM free=%u\n", (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
    log_printf("READY sensor=1 camera=0 mode=irq_on_demand\n");
    log_printf("MODO foto_por_trigger=1 video=0 stream=removido\n");
    log_printf("CAPTURE_MODE on_demand=1 command=CMD_CAPTURE\n");
    log_printf("TRANSPORT mode=%s chunk=%d\n", transport_bin ? "bin" : "text", BIN_CHUNK);

    vTaskDelay(pdMS_TO_TICKS(SENSOR_ARM_SETTLE_MS));
    int level = gpio_get_level(SENSOR_GPIO);
    if (level == 1) {
        ESP_ERROR_CHECK(gpio_isr_handler_add(SENSOR_GPIO, sensor_isr, NULL));
        sensor_armed = true;
        log_printf("SENSOR_ARMED level=1 settle_ms=%d\n", SENSOR_ARM_SETTLE_MS);
    } else {
        log_printf("SENSOR_NOT_ARMED level=%d reason=not_at_rest\n", level);
    }

    BaseType_t rx_task_ok = xTaskCreatePinnedToCore(serial_rx_task, "serial_rx", 4096, NULL, 5, NULL, 0);
    BaseType_t capture_task_ok = xTaskCreatePinnedToCore(capture_task, "capture", 8192, NULL, 6, NULL, 1);
    if (rx_task_ok != pdPASS || capture_task_ok != pdPASS) {
        log_printf("TASKS_FAIL serial_rx=%d capture=%d\n", rx_task_ok, capture_task_ok);
        return;
    }
    log_printf("TASKS_READY serial_rx=core0 capture=core1 gpio4=LOW irq_queue=1 armed=%d\n", sensor_armed);
    vTaskDelete(NULL);
}
