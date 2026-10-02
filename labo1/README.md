# ESP-NOW over Pluto

The XIAO ESP32-C3 broadcasts four values over ESP-NOW on Wi-Fi channel 1
(2412 MHz). Packets are sent at 6 Mbps OFDM so the GNU Radio 802.11g receiver
can decode them. ESP-NOW is packet-based, so SDR++ shows bursts rather than a
continuous carrier.

## Build and flash the ESP32

From PowerShell in the project root:

```powershell
pio run -d labo1
pio run -d labo1 -t upload
pio device monitor -d labo1
```

The serial monitor reports each broadcast sequence and value.

## View the transmission in SDR++

Stop the Python receiver first, then tune SDR++ to 2412 MHz with about 20 MHz
of visible bandwidth. Look for packet bursts near channel 1. SDR++ and the
Python receiver should not use the Pluto at the same time.

## Decode packets with the Pluto

Open Ubuntu WSL2, then run:

```bash
cd /mnt/c/Users/felix/Documents/Master2_ECAM/RF_project/labo1
bash setup_gnuradio_wsl.sh
python3 pluto_espnow_rx.py --uri ip:192.168.2.1
```

The setup script installs GNU Radio and builds `gr-ieee802-11` and Analog
Devices' `gr-iio` Pluto source blocks. It asks for `sudo` permission. Change the
URI if the Pluto is reachable through a different libiio connection. The Python
receiver prints decoded sequence numbers, dataset indexes, values, and missed
packet counts.

Use a low-power, short-range test setup. The RF receiver has to be tuned to the
same channel, and the Pluto must be reachable from WSL over libiio.