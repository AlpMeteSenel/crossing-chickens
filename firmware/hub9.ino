// SWARMFLOW sensor_hub v9: light/PIR, AHT20 Wire0, Movement Wire1, 30 WS2813 D6
#include "Arduino_RouterBridge.h"
#include <Wire.h>
#include <Arduino_Modulino.h>
#include "Ws2813D6.h"
#include "Aht20Decode.h"
#include "LedEffects.h"
#include <atomic>

#define NUM_LEDS 30
Ws2813D6 strip;

const int PIN_LIGHT = A0;
const int PIN_PIR   = D2;
const uint8_t AHT_ADDR = 0x38;

ModulinoMovement movement;
bool aht_ok = false;
bool imu_ok = false;
uint8_t aht_last_frame[6]{};
uint32_t aht_last_sample_ms = 0;

std::atomic<int> mode{6};
LedEffects::Settings effect_settings;
k_mutex effect_mutex;
std::atomic<uint32_t> manual_rgb{0};

uint32_t wheel(uint8_t p) {
  p = 255 - p;
  if (p < 85)  return ((uint32_t)(255 - p * 3) << 16) | ((uint32_t)(p * 3) << 8);
  p -= 85;
  if (p < 85)  return ((uint32_t)(p * 3) << 8) | (uint32_t)(255 - p * 3);
  p -= 85;
  return ((uint32_t)(p * 3) << 16) | (uint32_t)(255 - p * 3);
}
uint32_t effect_ambient(int raw) {
  uint8_t bri = map(constrain(raw, 0, 16383), 0, 16383, 90, 4);
  uint8_t cool = map(constrain(raw, 0, 16383), 0, 16383, 0, 180);
  strip.fill(bri, bri / 3 + 15, 20 + cool);
  return 50;
}
uint32_t effect_rainbow(uint32_t f) {
  for (int i = 0; i < NUM_LEDS; i++) {
    uint32_t c = wheel((i * 256 / NUM_LEDS + f * 4) & 0xFF);
    strip.setPixel(i, c >> 16, c >> 8, c);
  }
  return 40;
}
uint32_t effect_breathe(uint32_t f) {
  uint8_t b = 128 + (int8_t)(127.0 * sinf((f * 4 / 255.0f) * 2 * PI));
  uint32_t c = wheel((f / 20) & 0xFF);
  strip.fill((c >> 16) * b / 255, (c >> 8) * b / 255, (c & 255) * b / 255);
  return 60;
}
uint32_t effect_kitt(uint32_t f) {
  int period = 2 * (NUM_LEDS - 1);
  int p = f % period;
  int pos = p < NUM_LEDS ? p : period - p;
  strip.fill(0, 0, 0);
  for (int d = -2; d <= 2; d++) {
    int i = pos + d;
    if (i < 0 || i >= NUM_LEDS) continue;
    uint8_t v = 255 - 4 * abs(d);
    strip.setPixel(i, v, v / 8, 0);
  }
  return 60;
}
uint32_t effect_warn(uint32_t f) {
  strip.fill((f % 6) < 3 ? 255 : 0, (f % 6) < 3 ? 170 : 0, 0);
  return 50;
}
uint32_t effect_alert(uint32_t f) {
  bool on = (f % 4) < 2;
  strip.fill(on ? 255 : 0, 0, 0);
  return 50;
}
uint32_t effect_hazard(uint32_t f) {
  bool on = (f % 10) < 5;
  for (int i = 0; i < NUM_LEDS; i++) {
    bool left = i < NUM_LEDS / 2;
    strip.setPixel(i, (left == on) ? 255 : 0, (left == on) ? 170 : 0, 0);
  }
  return 50;
}
uint32_t effect_siren(uint32_t f) {
  bool a = (f % 8) < 4;
  for (int i = 0; i < NUM_LEDS; i++) {
    bool left = i < NUM_LEDS / 2;
    if (left == a) strip.setPixel(i, 255, 0, 0); else strip.setPixel(i, 0, 0, 255);
  }
  return 50;
}

bool aht_init() {
  Wire.beginTransmission(AHT_ADDR);
  Wire.write(0xBE); Wire.write(0x08); Wire.write(0x00);
  if (Wire.endTransmission()) return false;
  delay(20);
  Wire.requestFrom((int)AHT_ADDR, 1);
  if (!Wire.available()) return false;
  const uint8_t status = Wire.read();
  return !(status & 0x80) && (status & 0x08);
}
bool aht_read(float& t, float& h) {
  Wire.beginTransmission(AHT_ADDR);
  Wire.write(0xAC); Wire.write(0x33); Wire.write(0x00);
  if (Wire.endTransmission()) return false;
  delay(90);
  if (Wire.requestFrom((int)AHT_ADDR, 6) != 6) return false;
  uint8_t b[6];
  for (int i = 0; i < 6; i++) b[i] = Wire.read();
  Aht20Reading reading;
  if (!decodeAht20(b, sizeof(b), reading)) return false;
  h = reading.humidity; t = reading.temperature;
  for (unsigned i=0;i<6;++i) aht_last_frame[i]=b[i];
  aht_last_sample_ms=millis();
  return true;
}

String read_sensors() {
  char buf[400], temperature[16]="null", humidity[16]="null";
  float t = 0, h = 0, ax = 0, ay = 0, az = 0, gx = 0, gy = 0, gz = 0;
  const bool sample_ok = aht_ok && aht_read(t, h);
  if (sample_ok) {
    snprintf(temperature,sizeof(temperature),"%.1f",t);
    snprintf(humidity,sizeof(humidity),"%.1f",h);
  }
  if (imu_ok && movement.update()) {
    ax = movement.getX(); ay = movement.getY(); az = movement.getZ();
    gx = movement.getRoll(); gy = movement.getPitch(); gz = movement.getYaw();
  }
  snprintf(buf, sizeof(buf),
    "{\"light\":%d,\"pir\":%s,\"temp_c\":%s,\"hum_pct\":%s,\"aht_ok\":%s,\"ax\":%.2f,\"ay\":%.2f,\"az\":%.2f,\"gx\":%.1f,\"gy\":%.1f,\"gz\":%.1f,\"led_mode\":%d,\"brightness_percent\":%d,\"ts\":%lu}",
    analogRead(PIN_LIGHT),
    digitalRead(PIN_PIR) == HIGH ? "true" : "false",
    temperature, humidity, sample_ok ? "true" : "false", ax, ay, az, gx, gy, gz, mode.load(), strip.brightnessPercent(), millis());
  return String(buf);
}
String aht_debug() {
  char buf[160];
  snprintf(buf,sizeof(buf),"{\"frame\":[%u,%u,%u,%u,%u,%u],\"sample_ms\":%lu,\"initialized\":%s}",
    aht_last_frame[0],aht_last_frame[1],aht_last_frame[2],aht_last_frame[3],aht_last_frame[4],aht_last_frame[5],aht_last_sample_ms,aht_ok?"true":"false");
  return String(buf);
}

String i2c_scan() {
  char buf[128];
  int n = 0;
  buf[0] = 0;
  Wire.begin();
  for (uint8_t a = 8; a < 120 && n < 120; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) n += snprintf(buf + n, sizeof(buf) - n, " %02x", a);
  }
  return String(buf);
}

bool set_effect_config(int primary, int secondary, int speed, int width) {
  if (primary<0||primary>0xffffff||secondary<0||secondary>0xffffff||speed<25||speed>200||width<1||width>15) return false;
  k_mutex_lock(&effect_mutex, K_FOREVER);
  effect_settings.primary={uint8_t(primary>>16),uint8_t(primary>>8),uint8_t(primary)};
  effect_settings.secondary={uint8_t(secondary>>16),uint8_t(secondary>>8),uint8_t(secondary)};
  effect_settings.speed=speed;effect_settings.width=width;
  k_mutex_unlock(&effect_mutex);
  return true;
}
String led_pin_test() {
  const auto t=strip.selftest();char buf[180];
  snprintf(buf,sizeof(buf),"{\"high\":%d,\"low\":%d,\"high_error\":%d,\"low_error\":%d,\"configuration_ok\":%s}",t.high,t.low,t.highError,t.lowError,strip.configurationValid()?"true":"false");
  return String(buf);
}
bool set_mode(int m) {
  if (strip.error() < 0 || m < 0 || m > LedEffects::Last) return false;
  mode = m; return true;
}
bool set_led(int r, int g, int b) {
  if (strip.error() < 0) return false;
  manual_rgb = ((uint32_t)constrain(r,0,255) << 16) | ((uint32_t)constrain(g,0,255) << 8) | constrain(b,0,255);
  mode = 10;
  return true;
}
String led_status() {
  k_mutex_lock(&effect_mutex,K_FOREVER);const auto settings=effect_settings;k_mutex_unlock(&effect_mutex);
  char buf[450];
  snprintf(buf, sizeof(buf), "{\"pin\":\"D6/PB1\",\"pixels\":30,\"brightness_percent\":%d,\"driver_error\":%d,\"configuration_ok\":%s,\"frames_sent\":%lu,\"firmware\":\"hub9\",\"mode\":%d,\"max_animation_mode\":33,\"primary\":%lu,\"secondary\":%lu,\"speed\":%u,\"wave_width\":%u}",
    strip.brightnessPercent(), strip.error(), strip.configurationValid() ? "true" : "false", (unsigned long)strip.frames(), mode.load(),
    (unsigned long)((settings.primary.r<<16)|(settings.primary.g<<8)|settings.primary.b),
    (unsigned long)((settings.secondary.r<<16)|(settings.secondary.g<<8)|settings.secondary.b),settings.speed,settings.width);
  return String(buf);
}
bool set_brightness(int percent) {
  if (strip.error() < 0) return false;
  return strip.setBrightness(percent);
}

void setup() {
  k_mutex_init(&effect_mutex);
  strip.begin();
  strip.fill(0, 0, 0);
  Bridge.begin();
  Bridge.provide("read_sensors", read_sensors);
  Bridge.provide("aht_debug", aht_debug);
  Bridge.provide("set_led", set_led);
  Bridge.provide("set_mode", set_mode);
  Bridge.provide("led_status", led_status);
  Bridge.provide("set_effect_config", set_effect_config);
  Bridge.provide("led_pin_test", led_pin_test);
  Bridge.provide("set_brightness", set_brightness);
  Bridge.provide("i2c_scan", i2c_scan);
  pinMode(PIN_PIR, INPUT);
  Wire.begin();
  Modulino.begin();
  imu_ok = movement.begin();
  aht_ok = aht_init();
}

void loop() {
  static uint32_t f = 0;
  static int previous_mode = -1;
  const int current_mode = mode.load();
  if (current_mode != previous_mode) { f = 0; previous_mode = current_mode; }
  if (!aht_ok && (f % 100) == 0) aht_ok = aht_init();
  uint32_t d;
  switch (current_mode) {
    case 6: strip.fill(0,0,0); d = 100; break;
    case 1:  d = effect_rainbow(f); break;
    case 2:  d = effect_breathe(f); break;
    case 3:  d = effect_kitt(f);    break;
    case 11: d = effect_warn(f); break;
    case 12: d = effect_alert(f); break;
    case 13: d = effect_hazard(f); break;
    case 14: d = effect_siren(f); break;
    case 15: case 16: case 17: case 18: case 19: case 20: case 21:
    case 22: case 23: case 24: case 25: case 26: case 27: case 28: case 29: case 30: case 31: case 32: case 33: {
      k_mutex_lock(&effect_mutex,K_FOREVER);const auto settings=effect_settings;k_mutex_unlock(&effect_mutex);
      d=LedEffects::render(strip,current_mode,f,settings);break;
    }
    case 7: strip.fill(255,0,0); d = 100; break;
    case 8: strip.fill(0,255,0); d = 100; break;
    case 9: strip.fill(0,0,255); d = 100; break;
    case 10: { const uint32_t c = manual_rgb.load(); strip.fill(c >> 16, c >> 8, c); d = 100; break; }
    default: d = effect_ambient(analogRead(PIN_LIGHT)); break;
  }
  strip.show();
  f++;
  delay(d);
}
