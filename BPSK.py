import adi
import numpy as np
import matplotlib.pyplot as plt
import time

sdr = adi.Pluto(uri="usb:1.15.5")

# ---- Paramètres ----
fc = 2_400_000_000          # fréquence porteuse (TX et RX)
fs = 1_000_000            # fréquence d'échantillonnage
sps = 8                   # échantillons par symbole -> débit symbole = 125 kHz
N = 1024                  # nombre de bits dans la trame (répétée en boucle)

# Coupe un éventuel DDS (CW) resté actif des tests précédents
sdr.dds_single_tone(0, 0, channel=0)

# ---- Génération BPSK ----
rng = np.random.default_rng(42)
bits = rng.integers(0, 2, N)
symbols = 2 * bits - 1                      # 0 -> -1, 1 -> +1
tx_wave = np.repeat(symbols, sps).astype(complex)   # impulsion rectangulaire
tx_wave *= 2**14                            # échelle attendue par le DAC du Pluto

# ---- Config SDR ----
sdr.sample_rate = fs
sdr.tx_lo = fc
sdr.rx_lo = fc
sdr.tx_rf_bandwidth = fs
sdr.rx_rf_bandwidth = fs
sdr.tx_hardwaregain_chan0 = -30             # commence bas pour ne pas saturer le RX
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 20
sdr.rx_buffer_size = 3 * len(tx_wave)       # au moins une trame complète

# ---- Émission en boucle ----
sdr.tx_cyclic_buffer = True
sdr.tx(tx_wave)

time.sleep(0.5)
sdr.rx()                                    # vide le premier buffer
x = sdr.rx()
print(f"Amplitude max reçue : {np.max(np.abs(x)):.0f} (saturation vers 2000)")

# ---- Démodulation ----
# 1) Correction de phase (le carré supprime la modulation BPSK)
phi = 0.5 * np.angle(np.sum(x**2))
x = x * np.exp(-1j * phi)

# 2) Filtre adapté (moyenne sur un symbole) + recherche de l'instant d'échantillonnage
mf = np.convolve(x, np.ones(sps), mode="valid")
best = max(range(sps), key=lambda o: np.mean(np.abs(mf[o::sps].real)))
rx_syms = mf[best::sps][:N] / sps

# 3) Alignement sur la trame connue (décalage cyclique + ambiguïté de signe)
corr = np.fft.ifft(np.fft.fft(rx_syms.real) * np.conj(np.fft.fft(symbols)))
k = np.argmax(np.abs(corr))
s = np.sign(corr[k].real)
rx_syms = np.roll(rx_syms, -k) * s / np.mean(np.abs(rx_syms.real))

rx_bits = (rx_syms.real > 0).astype(int)
ber = np.mean(rx_bits != bits)
print(f"BER = {ber:.4f}  ({np.sum(rx_bits != bits)} erreurs sur {N} bits)")

# ---- Affichage ----
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.5))
a1.scatter(rx_syms.real, rx_syms.imag, s=8, alpha=0.5)
a1.set_title(f"Constellation BPSK (BER = {ber:.4f})")
a1.set_xlabel("I"); a1.set_ylabel("Q"); a1.grid(True); a1.axis("equal")

spec = np.fft.fftshift(np.fft.fft(x * np.hanning(len(x))))
f = np.fft.fftshift(np.fft.fftfreq(len(x), 1 / fs))
a2.plot((fc + f) / 1e6, 20 * np.log10(np.abs(spec) + 1e-12))
a2.set_title("Spectre reçu"); a2.set_xlabel("Fréquence (MHz)")
a2.set_ylabel("dB"); a2.grid(True)
plt.tight_layout()
plt.show()

sdr.tx_destroy_buffer()