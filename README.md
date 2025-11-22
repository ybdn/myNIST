# myNIST

![myNIST logo](mynist/resources/icons/mynist.png)

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#installation) [![Build](https://img.shields.io/badge/build-PyInstaller-green.svg)](mynist.spec) [![License](https://img.shields.io/badge/license-Proprietary-orange.svg)](LICENSE)

Visualiseur/editeur avec interface 3 panneaux pour fichiers ANSI/NIST-ITL. myNIST s'appuie sur `nistitl` (Idemia) pour le parsing, PyQt5 pour l'UI et inclut un export Signa Multiple pre-configure.

## Sommaire

- [Fonctionnalites](#fonctionnalites)
- [Installation](#installation)
- [Demarrage rapide](#demarrage-rapide)
- [Utilisation](#utilisation)
- [Comparaison cote a cote](#comparaison-côte-à-côte)
- [Export Signa Multiple](#export-signa-multiple)
- [Raccourcis clavier](#raccourcis-clavier)
- [Build et distribution](#build-et-distribution)
- [Tests et qualite](#tests-et-qualite)
- [Structure du projet](#structure-du-projet)
- [Depannage rapide](#depannage-rapide)
- [Ressources](#ressources)
- [Licence](#licence)

## Fonctionnalites

- Interface 3 panneaux (arborescence des records, champs, image biometrie) avec drag & drop de fichiers.
- Support des records clefs : Type-2 texte, empreintes Type-4/13/14/15, images Type-10/17, autres images (Type-7/8/16/19/20).
- **Comparaison cote a cote** : chargez deux sources (NIST, image, PDF) pour les comparer visuellement.
  - Annotations typées et numérotées (MATCH/EXCLUSION/MINUTIA/CUSTOM) + compteur par type, suppression au clic.
  - Mode overlay (superposition) avec transparence réglable, et blink comparator (alternance rapide G/D).
  - Grille/règle calibrée et flip horizontal/vertical pour recaler visuellement.
  - Mesure de distance : mode mesure bi-clic (px et mm si calibré), effacement rapide.
  - Vues liées : zoom/pan synchronisés (checkbox "Lier les vues"), rotation 90/180/reset par image.
  - Calibration DPI : selectionnez 2 points + distance en mm pour determiner la resolution, puis resample au DPI cible.
  - Améliorations d’image : sliders luminosité/contraste/gamma, inversion par image.
  - Export JPG : capturez la comparaison annotee en un seul fichier.
- Export « Signa Multiple » pret a l'emploi : suppression 2.215 et remplacement 2.217 par `11707`.
- Export releve PDF decadactylaire (A4) a partir des images disponibles.
- Aide embarquee (About, info export) et barre d'outils avec icones generes dynamiquement.
- Support images WSQ (empreintes via NBIS `dwsq`) et JPEG2000 (via `imagecodecs`).
- Fonctionnement local/offline, sans backend.

## Installation

### Prerequis

- Windows 10+, macOS 10.14+ ou Linux (Ubuntu 20.04+).
- Python 3.8+ et `pip` si vous utilisez le code source.

### Option 1 : depuis les sources (developpeurs)

```bash
git clone <votre-repo>
cd myNIST
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Option 2 : binaire PyInstaller

- Construire l'executable : voir [Build et distribution](#build-et-distribution).
- Lancer `dist/mynist` (rendre executable si besoin : `chmod +x dist/mynist`).

## Demarrage rapide

```bash
# Lancer depuis les sources
python -m mynist
# ou
./run.sh

# Lancer l'executable
./dist/mynist
```

Ensuite ouvrez un fichier `.nist`, `.nst`, `.eft`, `.an2` (ou `.int`) via `Fichier > Ouvrir` ou en glisser-deposer sur la fenetre.

## Utilisation

- **Navigation** : panneau gauche = types/IDC, panneau central = champs non vides, panneau droit = image si applicable.
- **Details** : cliquez sur un record pour afficher ses champs et l'image correspondante.
- **Info export** : `Aide > Export Signa Multiple Info`.
- **A propos** : `Aide > About`.

## Comparaison côte à côte

La vue de comparaison permet d'afficher deux sources (fichiers NIST, images standard ou PDF) cote a cote pour analyse visuelle.

### Chargement des sources

1. Cliquez sur **Charger gauche** ou **Charger droite** pour selectionner un fichier.
2. Formats supportes : `.nist`, `.nst`, `.eft`, `.an2`, `.int`, `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`, `.pdf`.

### Barre d'outils Annotations

| Bouton               | Fonction                                                              |
| -------------------- | --------------------------------------------------------------------- |
| **Main**             | Mode deplacement (glisser pour naviguer, zoom molette)                |
| **Annoter**          | Mode annotation (clic = ajouter un point, clic sur point = supprimer) |
| **Effacer G/D**      | Supprime les annotations du cote gauche ou droit                      |
| **Tout effacer**     | Supprime toutes les annotations                                       |
| **Masquer/Afficher** | Toggle la visibilite des annotations                                  |
| **Exporter JPG**     | Capture les deux vues avec annotations en un seul fichier             |

### Calibration et Reechantillonnage

Permet de determiner et ajuster la resolution des images pour comparaison precise :

**Calibration (determination du DPI) :**

1. Cliquez sur **Calibrer (2 points)** pour le cote souhaite.
2. Cliquez deux points sur l'image (ex: extremites d'une regle ou distance connue).
3. Saisissez la distance reelle en mm dans la boite de dialogue.
4. Le DPI est calcule automatiquement : `DPI = pixels / (mm / 25.4)`.

**Reechantillonnage (changement de resolution) :**

1. Assurez-vous que l'image est calibree (DPI affiche).
2. Definissez le DPI cible dans le spinbox (72-1200, defaut 500).
3. Cliquez sur **Reechantillonner** pour redimensionner l'image a la resolution souhaitee.

## Export Signa Multiple

Automatise deux regles sur le premier record Type-2 :

- Suppression du champ `2.215`.
- Attribution du champ `2.217` a `11707`.

Procedure :

1. Ouvrez un fichier NIST.
2. `Fichier > Export Signa Multiple...` (`Ctrl+E`).
3. Choisissez le chemin de sortie (`.nist`, `.eft`, `.an2`).
4. Le fichier source reste intact; un nouveau fichier est cree.

## Raccourcis clavier

- `Ctrl+O` : ouvrir un fichier NIST.
- `Ctrl+E` : Export Signa Multiple.
- `Ctrl+W` : fermer le fichier courant.
- `Ctrl+Q` : quitter.

## Build et distribution

- **PyInstaller** : `pyinstaller mynist.spec` ou `./build.sh` pour nettoyer, installer et produire `dist/mynist`.
- **Installation systeme (Ubuntu)** : `sudo ./install_ubuntu.sh` installe dans `/opt/mynist`, cree l'entree de menu et le symlink `/usr/local/bin/mynist`.  
  Desinstallation : `sudo ./uninstall_ubuntu.sh`.
- **Spec personnalisable** : ajoutez imports/datas dans `mynist.spec` si necessaire.

## Tests et qualite

```bash
# Lancer les tests unitaires
pytest

# Via Makefile
make test        # pytest -v
make lint        # flake8
make format      # black
make test-coverage
```

Les tests couvrent les controllers et le modele NIST de base (`tests/`). Des fixtures minimales sont fournies dans `tests/fixtures/` (voir `docs/tests_fixtures.md`) pour tester Type-4/7/9/10/14/15, EFTS/INT et cas tronques; pas besoin du dossier `nist-files/` complet pour lancer `pytest`.

## Structure du projet

```text
myNIST/
├── mynist/                # Code applicatif (PyQt5)
│   ├── controllers/       # Ouverture/export, logique Signa Multiple
│   ├── models/            # Manipulation ANSI/NIST (nistitl)
│   ├── views/             # UI 3 panneaux, barre d'outils
│   ├── utils/             # Constantes, logging, config
│   └── resources/         # Icones, styles
├── docs/                  # Guides utilisateur/dev et specifications
├── tests/                 # Tests unitaires + fixtures
├── build.sh, run.sh       # Scripts build/launch
├── install_ubuntu.sh      # Installation systeme (desktop entry)
├── mynist.spec            # Configuration PyInstaller
└── requirements.txt       # Dependances (nistitl, PyQt5, Pillow, pyinstaller)
```

## Depannage rapide

- `ModuleNotFoundError: nistitl` : `pip install --upgrade nistitl`.
- PyQt5 manquant : `pip install --upgrade PyQt5`.
- WSQ non lisible : Installer NBIS (`dwsq` dans le PATH). JPEG2000 : `pip install imagecodecs`.
- L'executable ne demarre pas : recompiler sur la meme plateforme que la cible.
- Aucun record charge : verifier que le fichier est bien ANSI/NIST-ITL valide et lisible.

## Ressources

- Guide utilisateur : `docs/user_guide.md`
- Guide developpeur : `docs/developer_guide.md`
- Syntheses : `QUICKSTART.md`, `CHEATSHEET.md`, `GUIDE_VISUEL.md`
- Standard ANSI/NIST-ITL : https://www.nist.gov/itl/iad/image-group/ansinist-itl-standard-references

## Licence

Proprietary License - Tous droits reserves. Voir `LICENSE`.  
Auteur : Yoann Baudrin — Version `0.1.0`.
