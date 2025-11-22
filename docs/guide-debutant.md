# 📘 myNIST - Mémo Pour Les Nuls

> Guide ultra-simple pour utiliser myNIST sans prise de tête !

---

## 🎯 C'est Quoi myNIST ?

**myNIST** = Un programme qui lit des fichiers `.nist` (fichiers d'empreintes digitales)

**Ça fait quoi ?**
- Ouvre et affiche des fichiers NIST
- Montre les données (texte) et les images (empreintes)
- Peut modifier automatiquement certains champs (Export Signa Multiple)

---

## 🚀 DÉMARRAGE RAPIDE (3 minutes chrono)

### Étape 1 : Ouvrir un Terminal

Sur Ubuntu :
- Appuyez sur `Ctrl+Alt+T`
- OU cherchez "Terminal" dans le menu

### Étape 2 : Aller dans le Dossier

```bash
cd ~/Desktop/myNIST
```

### Étape 3 : Lancer le Programme

```bash
./run.sh
```

**C'EST TOUT !** 🎉 Le programme s'ouvre automatiquement.

---

## 📂 Première Utilisation

### Si `./run.sh` Ne Marche Pas

**Probablement** : Le fichier n'est pas exécutable

**Solution :**
```bash
chmod +x run.sh
chmod +x build.sh
./run.sh
```

### Si Ça Dit "command not found"

**Probablement** : Python n'est pas installé

**Solution :**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

Puis relancez :
```bash
./run.sh
```

---

## 🖥️ Utiliser le Programme

### Interface = 3 Zones

```
┌─────────────┬──────────────┬──────────────┐
│   GAUCHE    │    MILIEU    │    DROITE    │
│  (Records)  │   (Champs)   │   (Images)   │
│             │              │              │
│  Cliquez    │  Affiche les │  Affiche les │
│  sur un     │  données en  │  empreintes  │
│  record     │  tableau     │  digitales   │
└─────────────┴──────────────┴──────────────┘
```

### Ouvrir un Fichier NIST

1. **Menu** → `Fichier` → `Ouvrir un fichier NIST`
2. **Raccourci** : `Ctrl+O`
3. Sélectionnez votre fichier `.nist`
4. **Boom !** Le fichier s'affiche

### Voir les Données

1. **À gauche** : Cliquez sur un record (ex: Type-2)
2. **Au centre** : Les champs s'affichent automatiquement
3. **À droite** : L'image s'affiche (si le record en contient une)

### Export Signa Multiple

**C'est quoi ?**
- Une fonction qui modifie automatiquement 2 champs :
  - Supprime le champ `2.215`
  - Met `"11707"` dans le champ `2.217`

**Comment faire ?**

1. Ouvrez un fichier NIST
2. **Menu** → `Fichier` → `Export Signa Multiple`
3. **Raccourci** : `Ctrl+E`
4. Donnez un nom au nouveau fichier
5. Cliquez sur "Enregistrer"
6. **Terminé !** Un nouveau fichier est créé (l'ancien reste intact)

---

## 🛠️ Installation Complète (Si Nécessaire)

**Seulement si `./run.sh` ne fonctionne PAS du tout**

### Méthode Complète

```bash
# 1. Aller dans le dossier
cd ~/Desktop/myNIST

# 2. Créer un environnement virtuel
python3 -m venv venv

# 3. Activer l'environnement
source venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer le programme
python -m mynist
```

**Vous verrez `(venv)` au début de votre terminal** = C'est bon signe ✅

---

## 🏗️ Compiler en Exécutable (Programme .exe Linux)

**Pourquoi ?**
- Pour avoir un fichier unique qu'on peut lancer sans Python
- Plus facile à distribuer

**Comment ?**

```bash
# Méthode 1 : Script automatique
./build.sh

# Méthode 2 : Étape par étape
source venv/bin/activate
pip install pyinstaller
pyinstaller mynist.spec
```

**Résultat :**
- Un fichier `mynist` dans le dossier `dist/`
- Lancez-le : `./dist/mynist`

---

## ⌨️ Raccourcis Clavier

| Touche | Action |
|--------|--------|
| `Ctrl+O` | Ouvrir un fichier |
| `Ctrl+E` | Export Signa Multiple |
| `Ctrl+Q` | Quitter |

---

## 🆘 Problèmes Fréquents

### ❌ "Permission denied" quand je lance `./run.sh`

**Solution :**
```bash
chmod +x run.sh
./run.sh
```

### ❌ "ModuleNotFoundError: No module named 'nistitl'"

**Solution :**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ "Le fichier NIST ne s'ouvre pas"

**Vérifiez :**
- C'est bien un fichier `.nist` (ou `.eft`, `.an2`)
- Le fichier n'est pas corrompu
- Vous avez les droits de lecture : `ls -l fichier.nist`

### ❌ "L'image ne s'affiche pas"

**Normal si :**
- Le record ne contient pas d'image (Type-2 = texte seulement)
- C'est un Type 1, 2, 9 (pas d'images dans ces types)

**Images possibles dans :**
- Type 4, 10, 13, 14, 15, 17

### ❌ "command not found: python3"

**Installez Python :**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

## 📚 Commandes Essentielles à Retenir

```bash
# Aller dans le dossier
cd ~/Desktop/myNIST

# Lancer le programme (FACILE)
./run.sh

# Lancer le programme (MÉTHODE LONGUE)
source venv/bin/activate
python -m mynist

# Compiler
./build.sh

# Lancer l'exécutable
./dist/mynist
```

---

## 🎓 Résumé en 5 Points

1. **Lancer** : `cd ~/Desktop/myNIST && ./run.sh`
2. **Ouvrir fichier** : `Ctrl+O` → sélectionner `.nist`
3. **Voir données** : Cliquer sur record à gauche
4. **Export Signa** : `Ctrl+E` → enregistrer
5. **Quitter** : `Ctrl+Q`

---

## 🧩 Structure Simple

```
myNIST/
├── run.sh              ← LANCER LE PROGRAMME (cliquer ici)
├── build.sh            ← COMPILER (créer l'exécutable)
├── requirements.txt    ← Liste des dépendances
├── mynist/             ← Code source (ne pas toucher)
├── docs/               ← Documentation
└── dist/               ← Exécutable après compilation
    └── mynist          ← FICHIER À LANCER
```

---

## 💡 Astuces Pro

### Astuce 1 : Toujours Sauvegarder les Originaux
Avant d'utiliser Export Signa Multiple, **faites une copie** de votre fichier NIST original !

```bash
cp fichier.nist fichier_backup.nist
```

### Astuce 2 : Vérifier le Fichier Exporté
Après Export Signa Multiple :
1. Rouvrez le fichier exporté dans myNIST
2. Allez dans Type-2
3. Vérifiez que 2.215 a disparu
4. Vérifiez que 2.217 = "11707"

### Astuce 3 : Créer un Alias (Raccourci)
Pour lancer plus vite :

```bash
# Ajouter dans ~/.bashrc
echo 'alias mynist="cd ~/Desktop/myNIST && ./run.sh"' >> ~/.bashrc
source ~/.bashrc

# Maintenant, tapez juste :
mynist
```

---

## 📖 Documents Complets (Si Besoin)

Si vous voulez aller plus loin :

- **[QUICKSTART.md](QUICKSTART.md)** - Démarrage rapide technique
- **[README.md](README.md)** - Documentation complète
- **[docs/user_guide.md](docs/user_guide.md)** - Guide utilisateur détaillé (FR)
- **[docs/developer_guide.md](docs/developer_guide.md)** - Pour développeurs

---

## ✅ Checklist Rapide

**Première utilisation :**
- [ ] Terminal ouvert
- [ ] `cd ~/Desktop/myNIST`
- [ ] `chmod +x run.sh build.sh`
- [ ] `./run.sh`
- [ ] Programme ouvert ✅

**Utilisation normale :**
- [ ] `./run.sh`
- [ ] `Ctrl+O` → Ouvrir fichier
- [ ] Cliquer sur record
- [ ] Voir données ✅

**Export Signa Multiple :**
- [ ] Fichier NIST ouvert
- [ ] `Ctrl+E`
- [ ] Nommer le fichier
- [ ] Enregistrer ✅

---

## 🎯 En Cas de Panique

**Si RIEN ne marche :**

1. Supprimez le dossier `venv/` :
   ```bash
   rm -rf venv
   ```

2. Relancez l'installation complète :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -m mynist
   ```

3. Si toujours bloqué, vérifiez :
   ```bash
   python3 --version    # Doit afficher Python 3.8+
   pip --version        # Doit fonctionner
   ```

---

## 📞 Contact

**Auteur :** Yoann BAUDRIN
**Version :** 0.1.0
**Licence :** Propriétaire - Tous droits réservés

---

## 🎉 Bon Courage !

**myNIST est simple à utiliser. N'ayez pas peur !**

> "La seule façon d'apprendre, c'est d'essayer." 🚀

---

**Dernière mise à jour :** 2025-01-21
