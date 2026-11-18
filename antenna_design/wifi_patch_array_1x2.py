"""Réseau de deux patchs Wi-Fi 2,4 GHz avec EMerge (prototype académique).

Géométrie 1x2 à alimentation microstrip commune. Les dimensions de la
jonction en T constituent des valeurs initiales NON optimisées : la bande
Wi-Fi entière et l'adaptation 50 ohms restent à vérifier par simulation.

Inspiré des API de demo4_patch_antenna.py du projet EMerge.
"""

from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt
import emerge as em
from emerge.plot import smith

# ====================== PARAMÈTRES ======================
mm = 1e-3
GHz = 1e9
f_cible = 2.44175 * GHz
f_debut = 2.30 * GHz
f_fin = 2.60 * GHz
n_freq = 31  # augmenter à 61-101 après validation du maillage

# PCB / métal
h = 1.6 * mm
epsilon_r = 4.3
pcb_x = 140.0 * mm
pcb_y = 110.0 * mm
rayon_air = 130.0 * mm

# Patches : L = direction y, W = direction x
W = 37.71 * mm
L = 28.60 * mm
espacement = 61.0 * mm  # centre à centre

# Alimentation : dimensions approchées pour FR-4 (h=1.6 mm)
w50 = 3.0 * mm
w70 = 1.6 * mm
jeu_encoche = 1.0 * mm
prof_encoche = 10.0 * mm

# Routage microstrip (les lignes horizontales influencent l'impédance)
y_T = -38.0 * mm
long_transfo = 17.0 * mm
y_fin_transfo = y_T + long_transfo  # -21 mm
y_entree_pcb = -pcb_y / 2  # -55 mm

# ====================== FONCTIONS =======================
def rectangle(xmin, ymin, xmax, ymax):
    """Plaque sur z=0 ; coordonnées en mètres."""
    if xmax <= xmin or ymax <= ymin:
        raise ValueError('Dimensions de rectangle non positives')
    return em.geo.XYPlate(
        xmax - xmin,
        ymax - ymin,
        position=(xmin, ymin, 0),
    )


def patch_a_encoche(cx):
    """Patch rectangulaire, fentes d'isolation de part et d'autre du feed."""
    objet = rectangle(cx - W / 2, -L / 2, cx + W / 2, L / 2)
    gauche = rectangle(
        cx - w50 / 2 - jeu_encoche, -L / 2,
        cx - w50 / 2, -L / 2 + prof_encoche,
    )
    droite = rectangle(
        cx + w50 / 2, -L / 2,
        cx + w50 / 2 + jeu_encoche, -L / 2 + prof_encoche,
    )
    objet = em.geo.remove(objet, gauche)
    objet = em.geo.remove(objet, droite)
    return objet


# ====================== MODÈLE ==========================
model = em.Simulation('WiFi_24GHz_Patch_Array_1x2')

substrat = em.geo.Box(
    pcb_x, pcb_y, h,
    position=(-pcb_x / 2, -pcb_y / 2, -h),
)
substrat.set_material(em.Material(epsilon_r, color='EMERGE-DIEL', opacity=0.8))

air = em.geo.Sphere(rayon_air).background()

masse = em.geo.XYPlate(
    pcb_x, pcb_y,
    position=(-pcb_x / 2, -pcb_y / 2, -h),
)
masse.set_material(em.lib.PEC)

# ====================== PATCHS ==========================
x1, x2 = -espacement / 2, +espacement / 2
cuivre = patch_a_encoche(x1)

parties = [
    patch_a_encoche(x2),
    # Deux sections verticales approximativement à 70,7 ohms
    rectangle(x1 - w70 / 2, y_T, x1 + w70 / 2, y_fin_transfo),
    rectangle(x2 - w70 / 2, y_T, x2 + w70 / 2, y_fin_transfo),
    # Deux lignes vers l'encoche des patchs (connexion jusqu'à son fond)
    rectangle(x1 - w50 / 2, y_fin_transfo,
              x1 + w50 / 2, -L / 2 + prof_encoche),
    rectangle(x2 - w50 / 2, y_fin_transfo,
              x2 + w50 / 2, -L / 2 + prof_encoche),
    # Ligne horizontale du diviseur en T
    rectangle(x1 - w70 / 2, y_T - w50 / 2,
              x2 + w70 / 2, y_T + w50 / 2),
    # Ligne commune, depuis le bord bas du PCB
    rectangle(-w50 / 2, y_entree_pcb,
              +w50 / 2, y_T + w50 / 2),
]

for partie in parties:
    cuivre = em.geo.add(cuivre, partie)
cuivre.set_material(em.lib.PEC)

# Port vertical entre ligne commune et masse au bord inférieur du PCB
port = em.geo.Plate(
    np.array([-w50 / 2, y_entree_pcb, -h]),
    np.array([w50, 0, 0]),
    np.array([0, 0, h]),
)

# ====================== SIMULATION ======================
model.mw.set_resolution(0.15)
model.mw.set_frequency_range(f_debut, f_fin, n_freq)
model.commit_geometry()

# Refinement initial ; vérifier par convergence avant résultat final
model.mesher.set_boundary_size(cuivre, 2.0 * mm)
model.mesher.set_face_size(port, 0.8 * mm)
model.generate_mesh()

# Aperçus EMerge
model.view(selections=[port])

model.mw.bc.LumpedPort(
    port, 1, width=w50, height=h, direction=em.ZAX, Z0=50
)
frontiere = air.boundary()
model.mw.bc.AbsorbingBoundary(frontiere)
model.view(plot_mesh=True, volume_mesh=False)
model.view(bc=True)

print('Simulation du réseau 1x2 en cours...')
data = model.mw.run_sweep()

# ====================== RÉSULTATS =======================
frequences = np.asarray(data.scalar.grid.freq, dtype=float)
s11 = np.asarray(data.scalar.grid.model_S(1, 1, frequences))
s11_db = 20 * np.log10(np.maximum(np.abs(s11), 1e-15))

idx = np.argmin(s11_db)
print('\n===== RÉSULTATS DU RÉSEAU 1x2 =====')
print(f'Fréquence cible      : {f_cible/GHz:.5f} GHz')
print(f'Minimum S11 échant. : {frequences[idx]/GHz:.5f} GHz')
print(f'S11 minimum échant. : {s11_db[idx]:.2f} dB')

# Test sur les points simulés dans la bande Wi-Fi
bande = (frequences >= 2.400 * GHz) & (frequences <= 2.4835 * GHz)
if np.any(bande):
    print(f'Pire S11 dans la bande (points calculés) : '
          f'{np.max(s11_db[bande]):.2f} dB')
    print('Tous les points Wi-Fi échantillonnés sous -10 dB :',
          bool(np.all(s11_db[bande] <= -10.0)))
else:
    print('Aucun point de calcul dans la bande Wi-Fi.')

# Export CSV
sortie = Path(__file__).resolve().parent
csv_path = sortie / 'wifi_patch_array_1x2_s11.csv'
with csv_path.open('w', newline='', encoding='utf-8') as fichier:
    writer = csv.writer(fichier)
    writer.writerow(['frequence_GHz', 'S11_dB', 'Re_S11', 'Im_S11'])
    for f, db, s in zip(frequences, s11_db, s11):
        writer.writerow([f/GHz, db, np.real(s), np.imag(s)])
print('CSV :', csv_path)

# Courbe S11
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(frequences / GHz, s11_db, 'o-', label='Array 1x2')
ax.axhline(-10, linestyle='--', color='tab:red', label='Seuil -10 dB')
ax.axvspan(2.4, 2.4835, alpha=0.12, color='tab:green', label='Wi-Fi 2.4 GHz')
ax.axvline(f_cible / GHz, linestyle=':', color='tab:gray', label='Cible')
ax.set(xlabel='Fréquence (GHz)', ylabel='S11 (dB)',
       title='Réseau de deux patchs Wi-Fi — adaptation')
ax.grid(True)
ax.legend()
fig.tight_layout()
fig.savefig(sortie / 'wifi_patch_array_1x2_s11.png', dpi=170)

# Abaque de Smith (mêmes données simulées)
smith(s11, f=frequences, labels='S11')
plt.show()
