# myNIST - Guide de Démarrage Rapide

## Installation Rapide

### Depuis Ubuntu

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
python -m mynist

# OU utiliser le script de lancement
./run.sh
```

## Première Utilisation

### 1. Ouvrir un fichier NIST

- Lancez myNIST
- `Fichier > Ouvrir un fichier NIST` (ou `Ctrl+O`)
- Sélectionnez votre fichier `.nist`

### 2. Explorer le fichier

- **Panneau gauche** : Cliquez sur un record pour le sélectionner
- **Panneau central** : Visualisez les champs du record
- **Panneau droit** : Visualisez les images (si présentes)

### 3. Export Signa Multiple

Pour exporter avec les modifications automatiques :

- `Fichier > Export Signa Multiple` (ou `Ctrl+E`)
- Choisissez le nom du fichier de sortie
- Cliquez sur "Enregistrer"

**Modifications appliquées automatiquement :**
- Champ 2.215 : **SUPPRIMÉ**
- Champ 2.217 : **Remplacé par "11707"**

## Compilation en Exécutable

### Ubuntu uniquement

```bash
# Utiliser le script de build
./build.sh

# L'exécutable sera dans dist/mynist
./dist/mynist
```

## Arborescence du Projet

```text
myNIST/
├── mynist/              # Code source
│   ├── models/          # Modèles de données NIST
│   ├── views/           # Interface PyQt5
│   ├── controllers/     # Logique métier
│   └── utils/           # Utilitaires
├── tests/               # Tests unitaires
├── docs/                # Documentation
├── build.sh             # Script de compilation
├── run.sh               # Script de lancement
└── requirements.txt     # Dépendances Python
```

## Commandes Essentielles

```bash
# Lancer l'application
python -m mynist

# Lancer les tests
pytest

# Compiler l'exécutable
./build.sh

# Installer en mode développement
pip install -e .
```

## Raccourcis Clavier

| Action | Raccourci |
|--------|-----------|
| Ouvrir | `Ctrl+O` |
| Export Signa Multiple | `Ctrl+E` |
| Quitter | `Ctrl+Q` |

## Types de Fichiers Supportés

- `.nist` - Format NIST standard
- `.eft` - Electronic Fingerprint Transmission
- `.an2` - ANSI/NIST Type-2

## Aide et Documentation

- **Guide Utilisateur** : [docs/user_guide.md](docs/user_guide.md)
- **Guide Développeur** : [docs/developer_guide.md](docs/developer_guide.md)
- **README Complet** : [README.md](README.md)

## Dépannage Express

### Erreur d'import
```bash
pip install nistitl PyQt5 Pillow
```

### Fichier ne s'ouvre pas
- Vérifiez que c'est un fichier NIST valide
- Vérifiez les permissions

### L'exécutable ne fonctionne pas
- Compilez sur la même version d'Ubuntu que le système cible
- Utilisez `./build.sh` pour recompiler

## Support

En cas de problème :
1. Consultez les logs dans le terminal
2. Vérifiez la documentation complète
3. Vérifiez les dépendances : `pip list | grep -E "nistitl|PyQt5|Pillow"`

---

**Prêt à utiliser myNIST !** 🚀

Pour plus de détails, consultez le [README.md](README.md) complet.
