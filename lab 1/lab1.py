import adi
import numpy as np
import time

sdr = adi.Pluto(uri="ip:192.168.2.1")

# ---- Configuration TX : génère la CW ----
sdr.tx_lo = 433_000_000          # fréquence centrale TX
tone_freq = 100_000              # offset du ton DDS
tone_scale = 0.9

sdr.tx_hardwaregain_chan0 = -50  # atténué, adapte selon ton montage (câble/antenne)
sdr.dds_single_tone(tone_freq, tone_scale, channel=0)

print(f"CW émise en continu à {(sdr.tx_lo + tone_freq)/1e6:.4f} MHz")

# ---- Configuration RX : capture pour détecter la fréquence ----
sdr.rx_lo = 433_000_000          # centre RX (proche du signal attendu)
sdr.sample_rate = 2_000_000      # 2 MHz — doit couvrir l'offset du ton (100 kHz ici)
sdr.rx_rf_bandwidth = 2_000_000
sdr.rx_buffer_size = 4096
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 40    # ajuste selon ce que tu captes

time.sleep(0.5)  # laisse le temps aux réglages de se stabiliser
sdr.rx()          # premier appel souvent à vider (buffer de transition)

def detect_frequency():
    samples = sdr.rx()

    # FFT du signal complexe I/Q
    n = len(samples)
    spectrum = np.fft.fftshift(np.fft.fft(samples))
    freqs = np.fft.fftshift(np.fft.fftfreq(n, d=1/sdr.sample_rate))

    # Trouve le pic
    peak_idx = np.argmax(np.abs(spectrum))
    peak_offset = freqs[peak_idx]
    peak_power = 20 * np.log10(np.abs(spectrum[peak_idx]) + 1e-12)

    absolute_freq = sdr.rx_lo + peak_offset
    return absolute_freq, peak_offset, peak_power

try:
    while True:
        abs_freq, offset, power = detect_frequency()
        print(f"Fréquence détectée : {abs_freq/1e6:.4f} MHz "
              f"(offset {offset/1e3:+.1f} kHz, niveau {power:.1f} dB)")
        time.sleep(1)
except KeyboardInterrupt:
    sdr.tx_destroy_buffer()
    print("Arrêt")