import adi
import time

sdr = adi.Pluto(uri="usb:1.9.5")  # ou l'URI détectée automatiquement

# ---- TX : CW autour de 3 GHz ----
sdr.tx_lo = 2_400_000_000       # fréquence centrale TX : 3 GHz
tone_freq = 100_000             # offset du ton DDS
tone_scale = 0.9

sdr.tx_hardwaregain_chan0 = -20  # atténuation en dB (0 = puissance max)
sdr.dds_single_tone(tone_freq, tone_scale, channel=0)

print(f"Lecture de tx_lo appliqué : {sdr.tx_lo/1e9:.4f} GHz")
print(f"CW émise à {(sdr.tx_lo + tone_freq)/1e9:.6f} GHz")
print("Ctrl+C pour arrêter")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    sdr.tx_destroy_buffer()
    print("Émission arrêtée.")