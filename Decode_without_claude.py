import adi
import time
import numpy as np
import iio
import math

uri = next((u for u, d in iio.scan_contexts().items() if "PlutoSDR" in d), None)
if uri is None:
    raise RuntimeError("Aucun Pluto détecté.")
print("URI :", uri)
sdr = adi.ad9361(uri=uri)

fc = 2_442_000_000          # fréquence porteuse (TX et RX)
fs = 3_000_000            # fréquence d'échantillonnage
N = 4096                  # nombre de bits dans la trame (répétée en boucle)

sdr.sample_rate = fs
sdr.rx_lo = fc
sdr.rx_rf_bandwidth = fs
sdr.rx_enabled_channels = [0, 1]      # active RX1 et RX2
sdr.rx_buffer_size = N
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.rx_hardwaregain_chan0 = 40
sdr.rx_hardwaregain_chan1 = 40


time.sleep(0.5)
sdr.rx()
D = float(input("distance entre les deux antennes (m) : "))

l_onde = 299_792_458 / fc
k = 2*np.pi/l_onde

try:
    while True:
        x1, x2 = sdr.rx()

        # CHANGÉ : on ne garde que les échantillons où le paquet est présent
        p = np.abs(x1)**2 + np.abs(x2)**2
        mask = p > 10 * np.median(p)          # +10 dB au-dessus du bruit
        if mask.sum() < 50:
            continue                           # pas de paquet dans cette capture

        # CHANGÉ : un seul déphasage, calculé sur tout le paquet, déjà dans [-π, π]
        dphi = np.angle(np.sum(x2[mask] * np.conj(x1[mask])))

        for n in range(10):
            try:
                Theta = math.acos((dphi-n*2*np.pi)/(k*D))
            except ValueError:
                continue
            angle = np.degrees(Theta)
            print(f"Δφ = {np.degrees(dphi):7.1f}°  ->  angle = {angle:7.1f}°")
            break
except KeyboardInterrupt:
    pass


