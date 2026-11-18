
# ============================================================
# RESEAU DE DEUX PATCHS - GEOMETRIE INITIALE
# ============================================================

# Parametres communs
Wpatch = 37.71 * mm
Lpatch = 28.60 * mm

Wsub = 140.0 * mm
Lsub = 100.0 * mm
Rair = 130.0 * mm

d = 61.0 * mm       # Espacement centre-centre
w50 = 3.0 * mm      # Ligne 50 ohms (approx.)
w70 = 1.6 * mm      # Ligne 70.7 ohms (approx.)
inset = 10.0 * mm
gap = 1.0 * mm

# Substrat
substrate = em.geo.Box(
    Wsub, Lsub, h,
    position=(-Wsub/2, -Lsub/2, -h)
)

substrate.set_material(
    em.Material(er, color="EMERGE-DIEL", opacity=0.8)
)

# Domaine d'air
air = em.geo.Sphere(Rair).background()

# Masse
ground = em.geo.XYPlate(
    Wsub, Lsub,
    position=(-Wsub/2, -Lsub/2, -h)
)
ground.set_material(em.lib.PEC)


def rect(x1, y1, x2, y2):
    """Rectangle conducteur dans le plan z=0."""
    return em.geo.XYPlate(
        x2-x1, y2-y1,
        position=(x1, y1, 0)
    )


def create_patch(cx):
    """Patch avec encoche d'alimentation."""
    p = rect(
        cx-Wpatch/2, -Lpatch/2,
        cx+Wpatch/2, Lpatch/2
    )

    # Deux fentes de part et d'autre de la ligne
    left = rect(
        cx-w50/2-gap, -Lpatch/2,
        cx-w50/2, -Lpatch/2+inset
    )

    right = rect(
        cx+w50/2, -Lpatch/2,
        cx+w50/2+gap, -Lpatch/2+inset
    )

    p = em.geo.remove(p, left)
    p = em.geo.remove(p, right)
    return p


# Deux patchs
patch1 = create_patch(-d/2)
patch2 = create_patch(+d/2)

# Coordonnees du reseau d'alimentation
y_split = -36.0 * mm
y_transformer_end = -19.0 * mm
y_patch_feed = -Lpatch/2 + inset
y_port = -45.0 * mm

# Transformateurs 70.7 ohms
left_transformer = rect(
    -d/2-w70/2, y_split,
    -d/2+w70/2, y_transformer_end
)

right_transformer = rect(
    d/2-w70/2, y_split,
    d/2+w70/2, y_transformer_end
)

# Sections 50 ohms vers les encoches
left_feed = rect(
    -d/2-w50/2, y_transformer_end,
    -d/2+w50/2, y_patch_feed
)

right_feed = rect(
    d/2-w50/2, y_transformer_end,
    d/2+w50/2, y_patch_feed
)

# Diviseur en T
splitter = rect(
    -d/2, y_split-w50/2,
    d/2, y_split+w50/2
)

# Ligne principale 50 ohms
main_feed = rect(
    -w50/2, y_port,
    w50/2, y_split
)

# Union des conducteurs
copper = patch1
for part in [
    patch2,
    left_transformer,
    right_transformer,
    left_feed,
    right_feed,
    splitter,
    main_feed
]:
    copper = em.geo.add(copper, part)

copper.set_material(em.lib.PEC)

# Un seul port RF a l'entree de la ligne principale
port = em.geo.Plate(
    np.array([-w50/2, y_port, -h]),
    np.array([w50, 0, 0]),
    np.array([0, 0, h])
)
