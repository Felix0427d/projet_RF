
import numpy as np
import emerge as em
from emerge.plot import plot_sp, smith

# ============================================================
# 1. PARAMETRES
# ============================================================

mm = 1e-3
GHz = 1e9

f0 = 2.44175 * GHz
fmin = 2.20 * GHz
fmax = 2.70 * GHz
n_freq = 11

# Substrat FR-4
er = 4.3
h = 1.6 * mm

# Patch rectangulaire
Wpatch = 37.71 * mm
Lpatch = 29.24 * mm

# Alimentation par encoche
wline = 3.0 * mm
gap = 1.0 * mm
inset = 10.0 * mm

# Dimensions du domaine
Wsub = 80.0 * mm
Lsub = 80.0 * mm
Rair = 90.0 * mm

# ============================================================
# 2. SIMULATION
# ============================================================

model = em.Simulation("WiFi_24GHz_SinglePatch")

# ============================================================
# 3. GEOMETRIE
# ============================================================

# Substrat entre z = -h et z = 0
substrate = em.geo.Box(
    Wsub, Lsub, h,
    position=(-Wsub / 2, -Lsub / 2, -h)
)

substrate.set_material(
    em.Material(
        er,
        color="EMERGE-DIEL",
        opacity=0.8
    )
)

# Domaine d'air
air = em.geo.Sphere(Rair).background()

# Plan de masse sous le substrat
ground = em.geo.XYPlate(
    Wsub, Lsub,
    position=(-Wsub / 2, -Lsub / 2, -h)
)
ground.set_material(em.lib.PEC)

# Patch conducteur sur le substrat
patch = em.geo.XYPlate(
    Wpatch, Lpatch,
    position=(-Wpatch / 2, -Lpatch / 2, 0)
)

# Encoche gauche
cut_left = em.geo.XYPlate(
    gap, inset,
    position=(-wline / 2 - gap, -Lpatch / 2, 0)
)

# Encoche droite
cut_right = em.geo.XYPlate(
    gap, inset,
    position=(wline / 2, -Lpatch / 2, 0)
)

# Ligne conductrice au milieu de l'encoche
feed = em.geo.XYPlate(
    wline, inset,
    position=(-wline / 2, -Lpatch / 2, 0)
)

# Operations booleennes
patch = em.geo.remove(patch, cut_left)
patch = em.geo.remove(patch, cut_right)
patch = em.geo.add(patch, feed)
patch.set_material(em.lib.PEC)

# ============================================================
# 4. PORT RF 50 OHMS
# ============================================================

# Port vertical entre le patch et le plan de masse
port = em.geo.Plate(
    np.array([-wline / 2, -Lpatch / 2, -h]),
    np.array([wline, 0, 0]),
    np.array([0, 0, h])
)

# ============================================================
# 5. MAILLAGE
# ============================================================

model.mw.set_resolution(0.15)

model.mw.set_frequency_range(
    fmin, fmax, n_freq
)

model.commit_geometry()

# Raffinement local
model.mesher.set_boundary_size(
    patch, 2.0 * mm
)

model.mesher.set_face_size(
    port, 0.8 * mm
)

model.generate_mesh()

# Visualisation du modele
model.view(selections=[port])

# ============================================================
# 6. CONDITIONS AUX LIMITES
# ============================================================

# Port adapte a 50 ohms
port_bc = model.mw.bc.LumpedPort(
    port,
    1,
    width=wline,
    height=h,
    direction=em.ZAX,
    Z0=50
)

# Frontiere absorbante
boundary_selection = air.boundary()

abc = model.mw.bc.AbsorbingBoundary(
    boundary_selection
)

model.view(plot_mesh=True, volume_mesh=False)
model.view(bc=True)

# ============================================================
# 7. SIMULATION RF
# ============================================================

print("Demarrage de la simulation Wi-Fi 2.4 GHz")

data = model.mw.run_sweep()

# ============================================================
# 8. PARAMETRE S11
# ============================================================

freqs = np.asarray(data.scalar.grid.freq)

S11 = data.scalar.grid.model_S(
    1, 1, freqs
)

S11_dB = 20 * np.log10(
    np.maximum(np.abs(S11), 1e-15)
)

# Recherche du meilleur point d'adaptation echantillonne
idx = np.argmin(S11_dB)

print()
print("===== RESULTATS =====")
print(f"Frequence du minimum S11 : {freqs[idx]/GHz:.4f} GHz")
print(f"S11 minimum : {S11_dB[idx]:.2f} dB")
print(f"Objectif Wi-Fi : 2.400 - 2.4835 GHz")

print()
for f, s in zip(freqs, S11_dB):
    print(f"{f/GHz:.4f} GHz : {s:.2f} dB")

# Courbe S11 et abaque de Smith
plot_sp(freqs, S11)
smith(S11, f=freqs, labels="S11")
