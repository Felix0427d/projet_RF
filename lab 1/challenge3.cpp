#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

namespace {
constexpr uint8_t wifi_channel = 1;
constexpr uint8_t broadcast_address[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
constexpr int16_t data_set[] = {120, 240, 360, 480};
constexpr size_t data_set_size = sizeof(data_set) / sizeof(data_set[0]);
constexpr uint16_t packet_magic = 0x5246;

struct BroadcastPacket {
	uint16_t magic;
	uint32_t sequence;
	uint8_t sample_index;
	int16_t value;
} __attribute__((packed));

uint32_t sequence = 0;
}

void setup() {
	Serial.begin(115200);
	delay(500);

	WiFi.mode(WIFI_STA);
	WiFi.setSleep(false);

	if (esp_wifi_set_channel(wifi_channel, WIFI_SECOND_CHAN_NONE) != ESP_OK) {
		Serial.println("Failed to set Wi-Fi channel");
		while (true) {
			delay(1000);
		}
	}

	if (esp_now_init() != ESP_OK) {
		Serial.println("ESP-NOW initialization failed");
		while (true) {
			delay(1000);
		}
	}

	esp_now_peer_info_t peer = {};
	memcpy(peer.peer_addr, broadcast_address, sizeof(broadcast_address));
	peer.channel = wifi_channel;
	peer.ifidx = WIFI_IF_STA;
	peer.encrypt = false;

	if (esp_now_add_peer(&peer) != ESP_OK) {
		Serial.println("Failed to add ESP-NOW broadcast peer");
		while (true) {
			delay(1000);
		}
	}

	if (esp_wifi_config_espnow_rate(WIFI_IF_STA, WIFI_PHY_RATE_6M) != ESP_OK) {
		Serial.println("Failed to set ESP-NOW rate to 6 Mbps");
		while (true) {
			delay(1000);
		}
	}

	Serial.printf("ESP-NOW broadcast ready on channel %u (2412 MHz)\n", wifi_channel);
	Serial.println("ESP-NOW PHY rate: 6 Mbps OFDM");
	Serial.printf("Sender MAC: %s\n", WiFi.macAddress().c_str());
}

void loop() {
	const uint8_t sample_index = sequence % data_set_size;
	const BroadcastPacket packet = {
			packet_magic,
			sequence,
			sample_index,
			data_set[sample_index],
	};

	const esp_err_t result = esp_now_send(
			broadcast_address,
			reinterpret_cast<const uint8_t *>(&packet),
			sizeof(packet));

	if (result == ESP_OK) {
		Serial.printf("Broadcast seq=%lu index=%u value=%d\n",
									static_cast<unsigned long>(packet.sequence),
									packet.sample_index,
									packet.value);
	} else {
		Serial.printf("Broadcast failed: %d\n", static_cast<int>(result));
	}

	++sequence;
	delay(250);
}
