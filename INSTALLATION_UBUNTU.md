# 🐧 Installation Ubuntu - myNIST

Guide d'installation complète pour Ubuntu avec intégration au menu système.

---

## 📦 Méthode 1 : Installation Système (Recommandée)

Cette méthode installe myNIST dans `/opt/mynist/` et l'ajoute au menu Applications.

### Prérequis

```bash
# Ubuntu 20.04 ou supérieur
# Droits sudo
```

### Étapes

#### 1. Compiler l'Application

```bash
cd ~/Desktop/myNIST
./build.sh
```

L'exécutable sera créé dans `dist/mynist`

#### 2. Installer sur le Système

```bash
sudo ./install_ubuntu.sh
```

Le script va :
- ✅ Copier l'exécutable dans `/opt/mynist/`
- ✅ Copier l'icône dans `/opt/mynist/`
- ✅ Créer une entrée dans le menu Applications
- ✅ Créer un lien symbolique dans `/usr/local/bin/`

#### 3. Lancer l'Application

**Méthode A : Menu Applications**
1. Appuyez sur la touche Super (Windows)
2. Tapez "myNIST"
3. Cliquez sur l'icône

**Méthode B : Terminal**
```bash
mynist
```

**Méthode C : Chemin complet**
```bash
/opt/mynist/mynist
```

---

## 📂 Méthode 2 : Installation Utilisateur (Sans Sudo)

Installation dans votre répertoire personnel.

### Étapes

#### 1. Créer le Répertoire d'Installation

```bash
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons
```

#### 2. Copier l'Exécutable

```bash
cd ~/Desktop/myNIST
./build.sh
cp dist/mynist ~/.local/bin/
chmod +x ~/.local/bin/mynist
```

#### 3. Copier l'Icône

```bash
cp mynist/resources/icons/mynist.png ~/.local/share/icons/
```

#### 4. Créer l'Entrée Menu

```bash
cat > ~/.local/share/applications/mynist.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=myNIST
GenericName=NIST File Viewer
Comment=View and edit ANSI/NIST-ITL biometric files
Exec=$HOME/.local/bin/mynist
Icon=$HOME/.local/share/icons/mynist.png
Terminal=false
Categories=Utility;FileTools;Graphics;Science;
Keywords=NIST;biometric;fingerprint;viewer;forensic;
StartupWMClass=mynist
StartupNotify=true
MimeType=application/x-nist;application/x-eft;application/x-an2;
EOF
```

#### 5. Mettre à Jour le Cache

```bash
update-desktop-database ~/.local/share/applications/
```

#### 6. Ajouter au PATH (Optionnel)

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🗑️ Désinstallation

### Méthode Système

```bash
sudo ./uninstall_ubuntu.sh
```

### Méthode Utilisateur

```bash
rm -f ~/.local/bin/mynist
rm -f ~/.local/share/applications/mynist.desktop
rm -f ~/.local/share/icons/mynist.png
update-desktop-database ~/.local/share/applications/
```

---

## 🎨 Icône de l'Application

### Formats Disponibles

L'icône myNIST est disponible en plusieurs formats :

```
mynist/resources/icons/
├── mynist.svg          # Vectoriel (source)
├── mynist.png          # 512x512 (principal)
├── mynist.ico          # Multi-tailles (PyInstaller)
├── mynist_512.png      # 512x512
├── mynist_256.png      # 256x256
├── mynist_128.png      # 128x128
├── mynist_64.png       # 64x64
├── mynist_48.png       # 48x48
├── mynist_32.png       # 32x32
└── mynist_16.png       # 16x16
```

### Régénérer les Icônes

Si vous souhaitez modifier l'icône :

```bash
# Modifiez mynist/resources/icons/mynist.svg
# Puis régénérez les PNG et ICO :
python3 generate_icons_simple.py
```

---

## ✅ Vérification de l'Installation

### Vérifier l'Exécutable

```bash
which mynist
# Devrait afficher: /usr/local/bin/mynist ou ~/.local/bin/mynist
```

### Vérifier l'Entrée Menu

```bash
ls /usr/share/applications/mynist.desktop
# ou
ls ~/.local/share/applications/mynist.desktop
```

### Vérifier l'Icône

```bash
ls /opt/mynist/mynist.png
# ou
ls ~/.local/share/icons/mynist.png
```

### Tester le Lancement

```bash
mynist
```

L'application devrait s'ouvrir avec l'icône visible dans :
- La barre de titre de la fenêtre
- La barre des tâches Ubuntu
- Le menu Applications (si cherché)

---

## 🔧 Dépannage

### L'icône n'apparaît pas dans le menu

```bash
# Mettre à jour le cache desktop
sudo update-desktop-database /usr/share/applications/
# ou
update-desktop-database ~/.local/share/applications/

# Redémarrer GNOME Shell (Ubuntu avec GNOME)
killall -3 gnome-shell
```

### L'icône ne s'affiche pas dans la fenêtre

```bash
# Vérifier que l'icône existe
ls mynist/resources/icons/mynist.png

# Régénérer l'icône
python3 generate_icons_simple.py

# Recompiler
./build.sh
```

### La commande `mynist` n'est pas trouvée

```bash
# Méthode système
sudo ln -sf /opt/mynist/mynist /usr/local/bin/mynist

# Méthode utilisateur
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### L'application ne se lance pas

```bash
# Vérifier les permissions
chmod +x dist/mynist

# Lancer en mode debug
./dist/mynist

# Vérifier les dépendances
ldd dist/mynist
```

---

## 📊 Intégration Avancée

### Associer les Fichiers .nist

Pour ouvrir automatiquement les fichiers .nist avec myNIST :

```bash
# Ajouter à mynist.desktop :
MimeType=application/x-nist;application/x-eft;application/x-an2;

# Enregistrer le type MIME (créer si besoin)
mkdir -p ~/.local/share/mime/packages
cat > ~/.local/share/mime/packages/mynist.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-nist">
    <comment>NIST biometric file</comment>
    <glob pattern="*.nist"/>
    <icon name="mynist"/>
  </mime-type>
  <mime-type type="application/x-eft">
    <comment>Electronic Fingerprint Transmission</comment>
    <glob pattern="*.eft"/>
    <icon name="mynist"/>
  </mime-type>
  <mime-type type="application/x-an2">
    <comment>ANSI/NIST Type-2 file</comment>
    <glob pattern="*.an2"/>
    <icon name="mynist"/>
  </mime-type>
</mime-info>
EOF

# Mettre à jour la base MIME
update-mime-database ~/.local/share/mime
```

### Raccourci Clavier Global

Pour créer un raccourci clavier système :

1. Ouvrir **Paramètres** → **Clavier** → **Raccourcis clavier personnalisés**
2. Créer un nouveau raccourci :
   - **Nom** : myNIST
   - **Commande** : `/opt/mynist/mynist` ou `mynist`
   - **Raccourci** : `Super+N` (ou votre choix)

---

## 📋 Résumé des Commandes

```bash
# Installation complète
./build.sh
sudo ./install_ubuntu.sh

# Lancement
mynist

# Désinstallation
sudo ./uninstall_ubuntu.sh

# Régénération icône
python3 generate_icons_simple.py
```

---

## 🎯 Checklist d'Installation

- [ ] Application compilée (`./build.sh`)
- [ ] Exécutable existe (`dist/mynist`)
- [ ] Installation effectuée (`sudo ./install_ubuntu.sh`)
- [ ] Commande `mynist` fonctionne
- [ ] Icône visible dans le menu Applications
- [ ] Icône visible dans la fenêtre de l'app
- [ ] Fichier .desktop présent
- [ ] Tests de lancement OK

---

**Auteur :** Yoann BAUDRIN
**Version :** 0.1.0
**Licence :** Propriétaire - Tous droits réservés

---

> 🐧 **myNIST est maintenant parfaitement intégré à Ubuntu !**
