# Projet RF

Ce projet utilise deux types de cartes :

- un ou deux ESP32-C3 comme émetteurs ;
- un SDR Pluto+ d'opensdrLab comme récepteur.

## Installation sous Windows

### ESP32-C3

L'ESP32-C3 peut être programmé depuis VS Code ou l'Arduino IDE.

### SDR Pluto+

Le Pluto+ n'a pas besoin d'être reprogrammé pour ce projet. Installez :

1. le [driver Pluto pour Windows](https://wiki.analog.com/university/tools/pluto/drivers/windows) ;
2. le [package libiio](https://github.com/analogdevicesinc/libiio/releases).

Le package libiio fournit le transport utilisé par les scripts Python. Le Pluto+
peut être connecté en Ethernet ou en USB-C. La connexion USB-C est recommandée
; elle évite de configurer une adresse réseau et convient mieux aux petites
installations.

Pour vérifier l'installation, utilisez [SDR++](https://github.com/AlexandreRouma/SDRPlusPlus/releases/tag/nightly),
réglez-le sur `101.1 MHz` (Tipik), puis vérifiez qu'une émission radio est
audible.

## Environnement Python

Depuis la racine du projet, installez les dépendances dans l'interpréteur Python
utilisé par VS Code :

```powershell
python -m pip install pyadi-iio numpy matplotlib pylibiio
```

`pyadi-iio` expose l'interface Python du Pluto (`import adi`) et s'appuie sur
libiio pour communiquer avec le matériel.

## Récupération automatique des données

Le script [intro/data_recovery.py](intro/data_recovery.py) configure le Pluto et
lit un bloc d'échantillons IQ :

```powershell
python intro/data_recovery.py
```

Par défaut, il utilise l'URI Ethernet `ip:192.168.2.1`. Pour une connexion USB,
libiio peut généralement détecter automatiquement le Pluto ; utilisez par
exemple `--uri usb:1.24.5` si plusieurs appareils USB sont présents.

Le backend série de libiio peut être sélectionné explicitement avec l'URI
correspondante, par exemple sous Windows :

```powershell
python intro/data_recovery.py --uri serial:COM3,115200
```

`COM3` doit être remplacé par le port attribué à votre carte. Cette URI concerne
le transport libiio ; un port série utilisé uniquement comme console n'est pas
un flux IQ indépendant.
