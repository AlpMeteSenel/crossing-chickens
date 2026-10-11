#pragma once
#include <stdint.h>
#include <stddef.h>

struct Aht20Reading { float temperature, humidity; };
inline bool decodeAht20(const uint8_t* b, size_t count, Aht20Reading& result) {
  if (count < 6 || (b[0] & 0x80) || !(b[0] & 0x08)) return false;
  const uint32_t humidity = (uint32_t(b[1]) << 12) | (uint32_t(b[2]) << 4) | (b[3] >> 4);
  const uint32_t temperature = (uint32_t(b[3] & 15) << 16) | (uint32_t(b[4]) << 8) | b[5];
  result.humidity = humidity * 100.0f / 1048576.0f;
  // AHT20 reports a 200-degree digital span (-50 to +150), not a 165-degree span.
  result.temperature = temperature * 200.0f / 1048576.0f - 50.0f;
  return true;
}
