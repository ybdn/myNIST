# ⚡ myNIST - Cheat Sheet Ultra-Rapide

## 🚀 Lancer le Programme (2 commandes)

```bash
cd ~/Desktop/myNIST
./run.sh
```

**C'est tout !** ✅

---

## 🎯 Utilisation en 4 Étapes

| Étape | Action | Raccourci |
|-------|--------|-----------|
| 1️⃣ | Ouvrir fichier NIST | `Ctrl+O` |
| 2️⃣ | Cliquer sur record (gauche) | - |
| 3️⃣ | Voir données (centre) et images (droite) | - |
| 4️⃣ | Export Signa Multiple | `Ctrl+E` |

---

## ⌨️ Raccourcis Essentiels

- **Ctrl+O** → Ouvrir
- **Ctrl+E** → Export Signa Multiple
- **Ctrl+Q** → Quitter

---

## 🛠️ Commandes Utiles

```bash
# Lancer
./run.sh

# Compiler (créer l'exécutable)
./build.sh

# Lancer l'exécutable
./dist/mynist

# Rendre exécutable (si erreur "Permission denied")
chmod +x run.sh build.sh
```

---

## 🆘 Dépannage Express

| Problème | Solution |
|----------|----------|
| Permission denied | `chmod +x run.sh` |
| Module not found | `pip install -r requirements.txt` |
| Python non trouvé | `sudo apt install python3 python3-pip` |
| Fichier ne s'ouvre pas | Vérifier que c'est bien un `.nist` |

---

## 📂 Interface = 3 Panneaux

```
┌──────────┬──────────┬──────────┐
│ GAUCHE   │ CENTRE   │ DROITE   │
│ Records  │ Données  │ Images   │
└──────────┴──────────┴──────────┘
```

---

## 💾 Export Signa Multiple

**Fait quoi ?**
- Supprime champ `2.215`
- Remplace `2.217` par `"11707"`

**Comment ?**
1. Ouvrir fichier → `Ctrl+E` → Enregistrer

---

## 📚 Docs Complètes

- **Simple** → [MEMO_POUR_LES_NULS.md](MEMO_POUR_LES_NULS.md)
- **Rapide** → [QUICKSTART.md](QUICKSTART.md)
- **Complet** → [README.md](README.md)

---

**Auteur :** Yoann BAUDRIN | **Licence :** Propriétaire
