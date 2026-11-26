import time
import adi
import iio
import numpy as np

F_SIGNAL = 2_412_000_000   # canal 1 de l'ESP32
F_OFF = 200_000            # décalage du LO
FS = 4_000_000
N = 2**16
GAIN = 20
SEUIL = 10                 # détection d'un paquet : 10 x la puissance médiane
N_CAL = 30                 # nombre de paquets utilisés

plutos = [u for u, d in iio.scan_contexts().items() if "PlutoSDR" in d]
uri = next((u for u in plutos if u.startswith("usb:")), plutos[0] if plutos else None)
sdr = adi.ad9361(uri=uri)

sdr.sample_rate = FS
sdr.rx_lo = F_SIGNAL - F_OFF
sdr.rx_rf_bandwidth = FS
sdr.rx_enabled_channels = [0, 1]
sdr.rx_buffer_size = N
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.rx_hardwaregain_chan0 = GAIN
sdr.rx_hardwaregain_chan1 = GAIN

sdr.rx()  # vide le premier buffer

unit = []
t0 = time.time()
while len(unit) < N_CAL and time.time() - t0 < 60:
    x1, x2 = sdr.rx()
    p = np.abs(x1) ** 2 + np.abs(x2) ** 2
    mask = p > SEUIL * np.median(p)
    if mask.sum() < 50:
        continue
    z = np.sum(x2[mask] * np.conj(x1[mask]))
    unit.append(z / abs(z))

cal = np.mean(unit)
print(f"{len(unit)} paquets | stabilité : {abs(cal):.3f}")
print(f"Déphasage RX2-RX1 : {np.degrees(np.angle(cal)):.1f}°")