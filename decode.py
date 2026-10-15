import adi
import time
import numpy as np

sdr = adi.ad9361(uri="usb:1.8.5")  # ou l'URI détectée automatiquement


FC = 2_437_000_000        # fréquence de la CW de l'ESP32-C3 (canal Wi-Fi 6)
LO_OFFSET = 200_000       # le LO est décalé pour que la CW tombe à +200 kHz (loin du pic DC)
FS = 2_000_000
N = 2**14
D = 0.0615                # espacement des antennes (m), <= lambda/2
LAMBDA = 299_792_458 / FC
SMOOTH = 0.7 


sdr.rx_enabled_channels = [0, 1]  # activer les deux canaux RX
sdr.sample_rate = FS
sdr.rx_lo = FC - LO_OFFSET
sdr.rx_rf_bandwidth = FS
sdr.rx_enabled_channels = [0, 1]
sdr.rx_buffer_size = N
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.rx_hardwaregain_chan0 = 40
sdr.rx_hardwaregain_chan1 = 40


freqs = np.fft.fftfreq(N, 1 / FS)
window = np.hanning(N)
band = np.abs(freqs - LO_OFFSET) < 100_000

time.sleep(0.5)
sdr.rx()

def measure(n_avg=10):
    """Retourne (phasor de déphasage voie2/voie1, amplitude max brute)."""
    acc = 0j
    vmax = 0
    for _ in range(n_avg):
        x1, x2 = sdr.rx()
        vmax = max(vmax, np.max(np.abs(x1)), np.max(np.abs(x2)))
        X1 = np.fft.fft(x1 * window)
        X2 = np.fft.fft(x2 * window)
        k = np.argmax((np.abs(X1) ** 2 + np.abs(X2) ** 2) * band)
        acc += X2[k] * np.conj(X1[k])   # le produit annule la phase commune aux deux voies
    return acc / abs(acc), vmax

cal, vmax = measure(50)

smooth = 1 + 0j
try:
    while True:
        ph, vmax = measure(10)
        ph = ph * np.conj(cal)                       # retire l'offset de calibration
        smooth = SMOOTH * smooth + (1 - SMOOTH) * ph # lissage sur le cercle (évite les sauts ±180°)
        dphi = np.angle(smooth)
        s = dphi * LAMBDA / (2 * np.pi * D)
        if abs(s) > 1:
            print(f"Δφ = {np.degrees(dphi):7.1f}°  ->  hors plage")
        else:
            print(f"Δφ = {np.degrees(dphi):7.1f}°  ->  angle = {np.degrees(np.arcsin(s)):6.1f}°")
        time.sleep(0.1)
except KeyboardInterrupt:
    pass