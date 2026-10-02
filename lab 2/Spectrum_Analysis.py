import adi
import time
import matplotlib.pyplot as plt
import numpy as np


sdr = adi.Pluto(uri="ip:pluto.local")

# ---- TX : génère la CW ----
sdr.tx_lo = 433_000_000
tone_freq = 100_000
tone_scale = 0.9

sdr.tx_hardwaregain_chan0 = -50  # ajuste selon ton montage (câble/antenne)
sdr.dds_single_tone(tone_freq, tone_scale, channel=0)
print(f"CW émise à {(sdr.tx_lo + tone_freq)/1e6:.4f} MHz")

# ---- RX : configuration ----
sdr.rx_lo = 433_000_000
sdr.sample_rate = 2_000_000
sdr.rx_rf_bandwidth = 2_000_000
sdr.rx_buffer_size = 4096
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 40

time.sleep(0.5)
sdr.rx()  # premier appel à vider (buffer de transition)

# ---- Préparation FFT / axes ----
window = np.hanning(sdr.rx_buffer_size)
freqs = np.fft.fftshift(np.fft.fftfreq(sdr.rx_buffer_size, d=1 / sdr.sample_rate))
absolute_freqs = (sdr.rx_lo + freqs) / 1e6  # en MHz

# ---- Affichage temps réel ----
plt.ion()
fig, ax = plt.subplots(figsize=(10, 5))
line, = ax.plot(absolute_freqs, np.zeros(sdr.rx_buffer_size))
peak_marker = ax.axvline(absolute_freqs[0], color="r", linestyle="--", alpha=0.5)
peak_text = ax.text(0.02, 0.95, "", transform=ax.transAxes, color="r")

ax.set_xlabel("Fréquence (MHz)")
ax.set_ylabel("Amplitude (dB)")
ax.set_title("Spectre en temps réel - Pluto SDR")
ax.set_ylim(-20, 100)  # ajuste selon tes niveaux observés
ax.grid(True)

print("Fermer la fenêtre du graphique pour arrêter.")

try:
    while plt.fignum_exists(fig.number):
        samples = sdr.rx()

        spectrum = np.fft.fftshift(np.fft.fft(samples * window))
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        peak_idx = np.argmax(power_db)
        peak_freq = absolute_freqs[peak_idx]

        line.set_ydata(power_db)
        peak_marker.set_xdata([peak_freq, peak_freq])
        peak_text.set_text(f"Pic: {peak_freq:.4f} MHz  ({power_db[peak_idx]:.1f} dB)")

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)

except KeyboardInterrupt:
    pass
finally:
    sdr.tx_destroy_buffer()
    print("Émission arrêtée.")