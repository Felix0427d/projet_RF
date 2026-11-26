import argparse
import struct

try:
    import pmt
    from gnuradio import gr, iio
    import ieee802_11
    from wifi_phy_hier import wifi_phy_hier
except ModuleNotFoundError as error:
    raise SystemExit(
        "GNU Radio's Python modules (including pmt) are missing. "
        "Run this receiver with Ubuntu WSL/Linux, not Windows Python. "
        "From labo1, run setup_gnuradio_wsl.sh first, then start it with "
        "python3 pluto_espnow_rx.py --uri ip:192.168.2.1."
    ) from error


CENTER_FREQUENCY = 2_412_000_000
SAMPLE_RATE = 20_000_000
PACKET_MAGIC = 0x5246
PACKET_FORMAT = struct.Struct("<HIBh")
MAGIC_BYTES = struct.pack("<H", PACKET_MAGIC)
EXPECTED_VALUES = (120, 240, 360, 480)


class EspNowPacketSink(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self, "espnow_packet_sink", [], [])
        self.port = pmt.intern("in")
        self.message_port_register_in(self.port)
        self.set_msg_handler(self.port, self.handle_pdu)
        self.last_sequence = None

    def handle_pdu(self, message):
        if not pmt.is_pair(message):
            return

        try:
            frame = bytes(pmt.to_python(pmt.cdr(message)))
        except (TypeError, ValueError):
            return

        offset = 0
        while True:
            offset = frame.find(MAGIC_BYTES, offset)
            if offset < 0:
                return

            if offset + PACKET_FORMAT.size <= len(frame):
                magic, sequence, sample_index, value = PACKET_FORMAT.unpack_from(frame, offset)
                if (
                    magic == PACKET_MAGIC
                    and sample_index < len(EXPECTED_VALUES)
                    and value == EXPECTED_VALUES[sample_index]
                ):
                    if self.last_sequence is not None:
                        missed = (sequence - self.last_sequence - 1) & 0xFFFFFFFF
                        if missed:
                            print(f"Paquets manqués : {missed}", flush=True)
                    self.last_sequence = sequence
                    print(
                        f"Donnée reçue : seq={sequence}, "
                        f"index={sample_index}, valeur={value}",
                        flush=True,
                    )
                    return

            offset += 1


class PlutoEspNowReceiver(gr.top_block):
    def __init__(self, uri, gain_db):
        gr.top_block.__init__(self, "Pluto ESP-NOW receiver")

        self.source = iio.pluto_source(
            uri,
            CENTER_FREQUENCY,
            SAMPLE_RATE,
            SAMPLE_RATE,
            0x8000,
            True,
            True,
            True,
            "manual",
            gain_db,
            "",
            True,
        )
        self.wifi_phy = wifi_phy_hier(
            bandwidth=SAMPLE_RATE,
            chan_est=ieee802_11.LS,
            encoding=ieee802_11.BPSK_1_2,
            frequency=CENTER_FREQUENCY,
            sensitivity=0.56,
        )
        self.packet_sink = EspNowPacketSink()

        self.connect(self.source, self.wifi_phy)
        self.msg_connect((self.wifi_phy, "mac_out"), (self.packet_sink, "in"))


def main():
    parser = argparse.ArgumentParser(description="Decode ESP-NOW packets from an ADALM-Pluto")
    parser.add_argument("--uri", default="ip:192.168.2.1", help="Pluto libiio URI")
    parser.add_argument("--gain", type=float, default=30.0, help="Pluto RX gain in dB")
    args = parser.parse_args()

    receiver = PlutoEspNowReceiver(args.uri, args.gain)
    print(
        "Listening on Wi-Fi channel 1 (2412 MHz, 20 MS/s). "
        "Press Ctrl+C to stop.",
        flush=True,
    )
    receiver.start()
    try:
        receiver.wait()
    except KeyboardInterrupt:
        pass
    finally:
        receiver.stop()
        receiver.wait()


if __name__ == "__main__":
    main()