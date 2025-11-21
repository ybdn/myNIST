# myNIST User Guide

## Introduction

myNIST est un visualiseur et éditeur de fichiers NIST (ANSI/NIST-ITL) conçu pour Ubuntu. Il permet de visualiser les données biométriques et d'exporter des fichiers avec des modifications spécifiques.

## Installation

### Prérequis

- Ubuntu 20.04 ou ultérieur
- Python 3.8 ou ultérieur (si vous utilisez le code source)

### Option 1 : Utiliser l'exécutable

Si vous avez reçu l'exécutable compilé :

```bash
# Rendre l'exécutable
chmod +x mynist

# Lancer l'application
./mynist
```

### Option 2 : Depuis le code source

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python -m mynist

# Ou utiliser le script
./run.sh
```

## Interface Utilisateur

L'interface de myNIST est divisée en 3 panneaux principaux :

### Panneau Gauche : Arborescence des Records

- Affiche la structure du fichier NIST
- Organisé par type de record (Type-1, Type-2, etc.)
- Cliquez sur un record pour afficher ses détails

### Panneau Central : Données des Champs

- Affiche tous les champs du record sélectionné
- Format : Tableau avec numéro de champ et valeur
- Seuls les champs non vides sont affichés

### Panneau Droit : Images Biométriques

- Affiche les empreintes digitales et autres images
- Zoom automatique pour s'adapter à la taille du panneau
- Supporte les Types 4, 13, 14, 15 (empreintes), 10 (visage), 17 (iris)

## Utilisation

### Ouvrir un Fichier NIST

1. **Menu** : Fichier > Ouvrir un fichier NIST
2. **Raccourci clavier** : `Ctrl+O`
3. Sélectionnez votre fichier (.nist, .eft, .an2)
4. Le fichier sera analysé et affiché

### Navigation dans le Fichier

1. Dans le panneau de gauche, développez les types de records
2. Cliquez sur un record spécifique
3. Les champs apparaissent au centre
4. Les images (si disponibles) apparaissent à droite

### Export Signa Multiple

Cette fonctionnalité permet d'exporter un fichier NIST avec des modifications spécifiques aux champs Type-2.

**Modifications appliquées :**
- Suppression du champ 2.215
- Remplacement du champ 2.217 par la valeur "11707"

**Procédure :**

1. Ouvrez un fichier NIST
2. **Menu** : Fichier > Export Signa Multiple
3. **Raccourci clavier** : `Ctrl+E`
4. Choisissez l'emplacement et le nom du fichier de sortie
5. Cliquez sur "Enregistrer"
6. Une boîte de dialogue confirme le succès de l'export

**Attention :** Le fichier original n'est jamais modifié. Un nouveau fichier est créé.

### Informations sur Export Signa Multiple

Pour voir les détails des modifications appliquées :

**Menu** : Aide > Export Signa Multiple Info

## Types de Records NIST Supportés

### Type-1 : Transaction Information
- Informations sur la transaction
- Métadonnées du fichier NIST

### Type-2 : User-Defined Descriptive Text
- Données alphanumériques
- Informations biographiques et démographiques
- **Important** : C'est le type modifié par "Export Signa Multiple"

### Type-4 : High-Resolution Grayscale Fingerprint
- Images d'empreintes digitales haute résolution
- Format niveaux de gris

### Type-13 : Variable-Resolution Latent Image
- Empreintes latentes à résolution variable

### Type-14 : Variable-Resolution Fingerprint Image
- Images d'empreintes à résolution variable

### Type-15 : Variable-Resolution Palmprint Image
- Images d'empreintes palmaires

### Type-10 : Facial & SMT Image
- Images de visages

### Type-17 : Iris Image
- Images d'iris

## Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl+O` | Ouvrir un fichier NIST |
| `Ctrl+E` | Export Signa Multiple |
| `Ctrl+Q` | Quitter l'application |

## Formats de Fichiers Supportés

- `.nist` - Format NIST standard
- `.eft` - Electronic Fingerprint Transmission
- `.an2` - ANSI/NIST Type-2

## Dépannage

### Le fichier ne s'ouvre pas

**Causes possibles :**
- Le fichier n'est pas au format ANSI/NIST-ITL valide
- Le fichier est corrompu
- Permissions insuffisantes

**Solutions :**
- Vérifiez que le fichier est bien un fichier NIST
- Vérifiez les permissions du fichier : `ls -l fichier.nist`
- Consultez les logs dans le terminal

### Les images ne s'affichent pas

**Causes possibles :**
- Le record ne contient pas d'images
- Format d'image non supporté
- Données d'image corrompues

**Solutions :**
- Vérifiez le type de record (doit être 4, 10, 13, 14, 15, ou 17)
- Consultez les messages d'erreur dans le panneau d'image

### Export Signa Multiple échoue

**Causes possibles :**
- Pas de record Type-2 dans le fichier
- Permissions d'écriture insuffisantes
- Espace disque insuffisant

**Solutions :**
- Vérifiez qu'un record Type-2 existe dans le fichier source
- Vérifiez les permissions du dossier de destination
- Vérifiez l'espace disque disponible

### L'application ne se lance pas

**Depuis l'exécutable :**
```bash
# Vérifier les permissions
chmod +x mynist

# Lancer depuis le terminal pour voir les erreurs
./mynist
```

**Depuis le code source :**
```bash
# Vérifier l'installation des dépendances
pip install -r requirements.txt

# Lancer avec messages de debug
python -m mynist
```

## Conseils d'Utilisation

### Visualisation Optimale

1. **Redimensionnez les panneaux** : Glissez les séparateurs entre panneaux pour ajuster la taille
2. **Sélection de records** : Utilisez le panneau de gauche pour naviguer rapidement
3. **Données importantes** : Les champs Type-2 contiennent généralement les informations biographiques

### Workflow Recommandé

1. Ouvrez le fichier NIST source
2. Vérifiez les données dans le panneau central
3. Visualisez les images dans le panneau droit
4. Si nécessaire, exportez avec "Export Signa Multiple"
5. Vérifiez le fichier exporté en le rouvrant

### Bonnes Pratiques

- **Sauvegardez vos fichiers originaux** avant toute modification
- **Testez l'export** sur un fichier de test avant utilisation en production
- **Vérifiez les logs** en cas de problème
- **Documentez vos modifications** pour traçabilité

## Support Technique

### Logs de l'Application

Les messages de log s'affichent dans le terminal si vous lancez l'application depuis la ligne de commande :

```bash
./mynist
# ou
python -m mynist
```

### Informations Système

Pour signaler un problème, incluez :
- Version d'Ubuntu : `lsb_release -a`
- Version de Python : `python3 --version`
- Version de myNIST : visible dans Aide > À propos
- Message d'erreur complet

## Glossaire

**ANSI/NIST-ITL** : American National Standards Institute / National Institute of Standards and Technology - Interchange for Latent. Standard pour l'échange de données biométriques.

**Type-2 Record** : Record contenant des données textuelles définies par l'utilisateur (informations biographiques).

**IDC** : Information Designation Character. Identifiant unique pour chaque record dans un fichier NIST.

**Champ** : Élément de données individuel dans un record NIST (ex: 2.215, 2.217).

**Export Signa Multiple** : Fonctionnalité spécifique de myNIST pour modifier automatiquement les champs 2.215 et 2.217.

## FAQ

**Q: Puis-je modifier d'autres champs que 2.215 et 2.217 ?**
R: La version actuelle ne permet que l'Export Signa Multiple avec règles fixes. Pour d'autres modifications, contactez le développeur.

**Q: Puis-je traiter plusieurs fichiers en même temps ?**
R: Non, myNIST traite un fichier à la fois. Pour le traitement par lot, utilisez des scripts shell.

**Q: Les fichiers NIST de tous les pays sont-ils supportés ?**
R: myNIST supporte le standard ANSI/NIST-ITL. Certaines implémentations nationales peuvent avoir des variations.

**Q: Puis-je ajouter des images au fichier NIST ?**
R: La version actuelle est en lecture seule (sauf Export Signa Multiple). L'ajout d'images n'est pas encore supporté.

**Q: Comment puis-je voir les champs vides ?**
R: Les champs vides ne sont pas affichés par défaut pour simplifier l'interface.

## À Propos

**myNIST** est un outil de visualisation et d'édition de fichiers NIST développé pour Ubuntu.

**Technologies utilisées :**
- nistitl (Idemia) : Parsing ANSI/NIST-ITL
- PyQt5 : Interface graphique
- Pillow : Traitement d'images

**Version** : 0.1.0

Pour plus d'informations, consultez le [README.md](../README.md) ou le [Guide Développeur](developer_guide.md).
