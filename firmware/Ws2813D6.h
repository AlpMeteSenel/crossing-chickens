#pragma once
#include <Arduino.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/irq.h>
#include <zephyr/kernel.h>
#include <cmsis_core.h>
#include <errno.h>
#include <atomic>

// UNO Q only: D6 = PB1. External pull-up is required. Never enable internal pulls.
// Physical WS2813 pulse widths still require verification at DIN.
class Ws2813D6 {
 public:
  static constexpr unsigned Pixels = 30;
  // Keep unscaled pixel colours; brightness changes also update a static frame.
  bool setBrightness(int percent) {
    if (percent < 0 || percent > 100) return false;
    k_mutex_lock(&mutex_, K_FOREVER);
    brightness_ = (percent * 255 + 50) / 100;
    brightnessPercent_ = percent;
    dirty_ = true;
    k_mutex_unlock(&mutex_);
    return true;
  }
  int brightnessPercent() const { return brightnessPercent_.load(); }
  int begin() {
    k_mutex_init(&mutex_);
    if (!device_is_ready(port())) return error_ = -ENODEV;
    // Include INPUT so diagnostics can read the physical level, not just latch state.
    error_ = gpio_pin_configure(port(), 1,
        GPIO_INPUT | GPIO_OUTPUT_INACTIVE | GPIO_OPEN_DRAIN);
    if (error_ < 0) return error_;
    if (!configurationValid()) return error_ = -EIO;
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    const uint32_t before = DWT->CYCCNT;
    for (volatile unsigned i = 0; i < 32; ++i) __NOP();
    if (DWT->CYCCNT == before) return error_ = -ENOTSUP;
    cyclesPerUs_ = SystemCoreClock / 1000000U;
    if (!cyclesPerUs_) return error_ = -EINVAL;
    return error_ = 0;
  }
  void fill(uint8_t r, uint8_t g, uint8_t b) {
    k_mutex_lock(&mutex_, K_FOREVER);
    for (unsigned i = 0; i < Pixels; ++i) {
      dirty_ |= data_[i * 3] != g || data_[i * 3 + 1] != r || data_[i * 3 + 2] != b;
      data_[i * 3] = g;
      data_[i * 3 + 1] = r;
      data_[i * 3 + 2] = b;
    }
    k_mutex_unlock(&mutex_);
  }
  void setPixel(unsigned i, uint8_t r, uint8_t g, uint8_t b) {
    if (i >= Pixels) return;
    k_mutex_lock(&mutex_, K_FOREVER);
    dirty_ |= data_[i * 3] != g || data_[i * 3 + 1] != r || data_[i * 3 + 2] != b;
    data_[i * 3] = g; data_[i * 3 + 1] = r; data_[i * 3 + 2] = b;
    k_mutex_unlock(&mutex_);
  }
  int show() {
    if (error_ < 0) return error_;
    if (!configurationValid()) return error_ = -EIO;
    k_mutex_lock(&mutex_, K_FOREVER);
    if (!dirty_) { k_mutex_unlock(&mutex_); return 0; }
    // Keep thread callbacks out of the waveform, but let hardware interrupts run
    // between bytes. Masking UART RX for a whole 0.94 ms frame loses ~11 bytes at
    // 115200 baud and can wedge the RouterBridge transport during animations.
    k_sched_lock();
    for (unsigned i = 0; i < sizeof(data_); ++i) {
      const uint8_t value = scale(data_[i]);
      const unsigned key = irq_lock();
      for (uint8_t mask = 0x80; mask; mask >>= 1) {
        const uint32_t start = DWT->CYCCNT;
        bsrr() = 1U << 1; // release line; resistor creates HIGH
        wait(start, (value & mask) ? ticks(900) : ticks(400));
        bsrr() = 1U << 17; // actively pull LOW
        wait(start, ticks(1300));
      }
      irq_unlock(key);
    }
    bsrr() = 1U << 17;
    k_sched_unlock();
    delayMicroseconds(350);
    ++frames_;
    dirty_ = false;
    k_mutex_unlock(&mutex_);
    return 0;
  }
  int setReleased(bool release) {
    if (error_ < 0) return error_;
    k_mutex_lock(&mutex_, K_FOREVER);
    const int result = gpio_pin_set(port(), 1, release ? 1 : 0);
    dirty_ = true;
    k_mutex_unlock(&mutex_);
    return result;
  }
  struct PinTest { int highError, lowError, high, low; };
  PinTest selftest() {
    k_mutex_lock(&mutex_, K_FOREVER);
    PinTest result;
    result.highError = setReleased(true);
    delay(2);
    result.high = level();
    result.lowError = setReleased(false);
    delay(2);
    result.low = level();
    k_mutex_unlock(&mutex_);
    return result;
  }
  int level() const { return gpio_pin_get(port(), 1); }
  int error() const { return error_; }
  uint32_t frames() const { return frames_; }
  uint32_t moder() const { return reg(0); }
  uint32_t otyper() const { return reg(4); }
  uint32_t pupdr() const { return reg(12); }
  bool configurationValid() const {
    return ((moder() >> 2) & 3U) == 1U &&
           (otyper() & 2U) && ((pupdr() >> 2) & 3U) == 0;
  }
 private:
  static const device* port() { return DEVICE_DT_GET(DT_NODELABEL(gpiob)); }
  static volatile uint32_t& reg(unsigned offset) {
    return *reinterpret_cast<volatile uint32_t*>(DT_REG_ADDR(DT_NODELABEL(gpiob)) + offset);
  }
  static volatile uint32_t& bsrr() { return reg(24); }
  uint8_t scale(uint8_t v) const { return (uint16_t(v) * brightness_ + 127) / 255; }
  uint32_t ticks(unsigned ns) const { return (cyclesPerUs_ * ns + 999) / 1000; }
  static void wait(uint32_t start, uint32_t cycles) {
    while (uint32_t(DWT->CYCCNT - start) < cycles) __NOP();
  }
  uint8_t data_[Pixels * 3]{};
  uint8_t brightness_ = 26;
  std::atomic<int> brightnessPercent_{10};
  uint32_t cyclesPerUs_ = 0, frames_ = 0;
  int error_ = -EAGAIN;
  k_mutex mutex_{};
  bool dirty_ = true;
};
