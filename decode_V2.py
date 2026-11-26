import adi
import time
import numpy as np
import iio
import math

plutos = [u for u, d in iio.scan_contexts().items() if "PlutoSDR" in d]
uri = next((u for u in plutos if u.startswith("usb:")), plutos[0] if plutos else None)
sdr = adi.ad9361(uri=uri)

fc = 2_442_000_000          # doit correspondre au canal utilisé par l'ESP32
fs = 3_000_000
N = 2**18                   # ≈ 87 ms par capture, pour attraper des paquets émis toutes les 250 ms
SEUIL = 20                  # amplitude brute minimale pour qu'un échantillon compte comme signal
N_CAL = 30                  # nombre de captures valides pour la calibration

D = float(input("distance entre les deux antennes (m) : "))

sdr.sample_rate = fs
sdr.rx_lo = fc
sdr.rx_rf_bandwidth = fs
sdr.rx_enabled_channels = [0, 1]
sdr.rx_buffer_size = N
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.rx_hardwaregain_chan0 = 10
sdr.rx_hardwaregain_chan1 = 10

l_onde = 299_792_458 / fc
k = 2 * np.pi / l_onde

sdr.rx()  # vide le premier buffer


def phase_masquee(x1, x2):
    """Somme x2*conj(x1) sur les seuls échantillons où le signal est présent.
    Retourne (z, nombre d'échantillons retenus), ou (None, 0) si aucun signal."""
    p = np.abs(x1) ** 2 + np.abs(x2) ** 2
    mask = p > SEUIL ** 2
    if mask.sum() < 50:
        return None, 0
    return np.sum(x2[mask] * np.conj(x1[mask])), int(mask.sum())


# ---------------- Calibration ----------------
unit = []
t0 = time.time()
while len(unit) < N_CAL and time.time() - t0 < 60:
    x1, x2 = sdr.rx()
    z, n_ech = phase_masquee(x1, x2)
    if z is None:
        continue                                # pas de paquet dans cette capture
    unit.append(z / abs(z))                     # vecteur unitaire, pas un angle

if len(unit) < 5:
    raise RuntimeError("Pas assez de signal pendant la calibration (ESP32 en émission ? SEUIL trop haut ?)")

cal = np.mean(unit)
cal = cal / abs(cal)                            # exp(j * déphasage de référence)
print(f"Déphasage de référence : {math.degrees(math.atan2(cal.imag, cal.real)):.1f}° "
      f"({len(unit)} captures)")

# ---------------- Mesure ----------------
try:
    while True:
        x1, x2 = sdr.rx()
        z, n_ech = phase_masquee(x1, x2)
        if z is None:
            continue                            # pas de paquet dans cette capture

        zc = z * np.conj(cal)                   # retire le déphasage de la carte
        dphi = math.atan2(zc.imag, zc.real)     # radians, dans [-π, π]

        angle = None
        for n in range(-2, 5):
            c = (dphi + 2 * math.pi * n) / (k * D)
            if abs(c) <= 1.15:                                    # tolérance pour le bruit et la calibration
                angle = math.degrees(math.asin(max(-1.0, min(1.0, c))))
                break

        if angle is None:
            print(f"Δφ = {math.degrees(dphi):7.1f}°  ->  hors plage   ({n_ech} éch.)")
        else:
            print(f"Δφ = {math.degrees(dphi):7.1f}°  ->  angle = {angle:7.1f}°   ({n_ech} éch.)")
        time.sleep(0.3)
except KeyboardInterrupt:
    pass
finally:
    sdr.rx_destroy_buffer()                     # libère le flux USB du Pluto