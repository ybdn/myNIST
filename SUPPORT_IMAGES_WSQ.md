# 🖼️ Support des Images WSQ dans myNIST

## 🔍 Problème Identifié

Vos fichiers NIST contiennent des **images au format WSQ** (Wavelet Scalar Quantization).

### Qu'est-ce que WSQ ?

- **Format** : Compression spécifique aux empreintes digitales
- **Standard** : Utilisé par le FBI et les forces de l'ordre
- **Signature** : Commence par `ffa0ffa8...`
- **Avantage** : Compression optimale pour empreintes (ratio 15:1 typique)

---

## ✅ Ce Qui a Été Corrigé

### 1. Détection des Images

**Avant :**
- ❌ Cherchait dans `DATA`, `data`, `image`
- ❌ Images non trouvées

**Après :**
- ✅ Cherche d'abord dans `_999` (champ standard pour Type-14/15)
- ✅ Images WSQ détectées et identifiées

### 2. Affichage des Images WSQ

**Maintenant :**
- ✅ Détecte automatiquement le format WSQ
- ✅ Affiche un message informatif si bibliothèque WSQ non installée
- ✅ Décode et affiche les images si bibliothèque WSQ disponible

---

## 📦 Installation du Support WSQ

### Option 1 : Script Automatique (Recommandé)

```bash
./install_wsq_support.sh
```

### Option 2 : Installation Manuelle

```bash
pip install wsq
```

**Note :** La bibliothèque `wsq` Python peut ne pas être disponible sur tous les systèmes.

---

## 🎯 Comportement Actuel

### Sans Bibliothèque WSQ

Quand vous cliquez sur un record avec image WSQ, vous verrez :

```
⚠️ WSQ Format Detected

This is a WSQ compressed fingerprint image.

To view WSQ images, install the wsq library:
   pip install wsq

Image size: 23987 bytes
Format: WSQ (Wavelet Scalar Quantization)

Note: WSQ is a standard compression format
for fingerprint images used by FBI and law enforcement.
```

### Avec Bibliothèque WSQ Installée

- ✅ L'image s'affiche directement
- ✅ Conversion automatique en niveaux de gris
- ✅ Redimensionnement automatique dans le panneau

---

## 🔧 Solutions Alternatives

### Si `pip install wsq` ne fonctionne pas

#### Solution 1 : NBIS (NIST Biometric Image Software)

Le logiciel officiel du NIST pour gérer WSQ.

**Installation :**
1. Télécharger depuis : https://www.nist.gov/itl/iad/image-group/products-and-services/image-group-open-source-server-nigos
2. Compiler et installer
3. Utiliser les utilitaires `dwsq` (decode) et `cwsq` (encode)

**Conversion WSQ → PNG :**
```bash
dwsq fingerprint.wsq -raw fingerprint.raw
raw2png fingerprint.raw fingerprint.png
```

#### Solution 2 : Conversion en Ligne

Plusieurs services en ligne permettent de convertir WSQ en PNG/JPEG (à utiliser avec précaution pour données sensibles).

#### Solution 3 : Logiciel NISTViewer

Le logiciel NISTViewer officiel supporte nativement WSQ.

---

## 📊 Formats d'Images Supportés

| Format | Support | Notes |
|--------|---------|-------|
| **JPEG** | ✅ Natif | Format commun |
| **PNG** | ✅ Natif | Format commun |
| **BMP** | ✅ Natif | Format Windows |
| **WSQ** | ⚠️ Optionnel | Nécessite bibliothèque `wsq` |
| **JPEG2000** | ❌ Non supporté | Utiliser PIL avec plugins |
| **JPEG-LS** | ❌ Non supporté | Utiliser pillow-jpls |

---

## 🧪 Test avec Vos Fichiers

### Test avec le Script de Debug

```bash
python3 debug_nist.py
```

**Ce que vous verrez :**
```
Type-14 (IDC 1):
  ✓ Found image data in '_999': 23987 bytes
    Format: Unknown (first bytes: ffa0ffa80002ffa4003a)
```

La signature `ffa0ffa8...` confirme WSQ.

---

## 💡 Recommandations

### Pour Visualiser Immédiatement

**Option A : Tester avec wsq :**
```bash
pip install wsq
python -m mynist
```

**Option B : Utiliser NISTViewer :**
- Télécharger NISTViewer (logiciel officiel)
- Ouvrir vos fichiers .nist
- Exporter les images en PNG
- Réimporter dans myNIST

### Pour Production

Si vous travaillez fréquemment avec des fichiers NIST contenant WSQ :

1. **Installer NBIS** (solution la plus robuste)
2. **Créer un script de conversion** :
   ```bash
   for file in *.wsq; do
     dwsq $file -raw ${file%.wsq}.raw
     raw2png ${file%.wsq}.raw ${file%.wsq}.png
   done
   ```

---

## 🐛 Debug

### Vérifier si WSQ est installé

```bash
python3 -c "import wsq; print('WSQ OK')"
```

**Si succès :**
```
WSQ OK
```

**Si échec :**
```
ModuleNotFoundError: No module named 'wsq'
```

### Vérifier le Format d'une Image

```bash
python3 -c "
import sys
with open('nist-files/102556281.nist', 'rb') as f:
    data = f.read()
    # Rechercher signature WSQ
    idx = data.find(b'\xff\xa0\xff\xa8')
    if idx >= 0:
        print(f'WSQ trouvé à position {idx}')
        print(f'Signature: {data[idx:idx+20].hex()}')
"
```

---

## 📝 Notes Techniques

### Champs NIST contenant des Images

- **Type-4** : Champ 9 (grayscale, déprécié)
- **Type-13** : Champ 999 (latent prints, WSQ/JPEG/PNG)
- **Type-14** : Champ 999 (fingerprints, WSQ/JPEG/PNG) ← **Vos fichiers**
- **Type-15** : Champ 999 (palmprints, WSQ/JPEG/PNG) ← **Vos fichiers**

### Pourquoi WSQ ?

- **Taux de compression** : 15:1 typique (vs 10:1 JPEG)
- **Qualité** : Optimisé pour les crêtes et sillons des empreintes
- **Standard** : FBI IAFIS depuis 1993
- **Spécification** : WSQ Gray-Scale Fingerprint Image Compression Specification

---

## ✅ Checklist de Vérification

- [ ] Images détectées dans le champ `_999`
- [ ] Format WSQ identifié (signature ffa0ffa8)
- [ ] Message informatif affiché dans myNIST
- [ ] Tentative d'installation : `pip install wsq`
- [ ] Test de l'application
- [ ] Images affichées OU message d'information clair

---

## 🔗 Ressources

- **NIST NBIS** : https://www.nist.gov/itl/iad/image-group/products-and-services/image-group-open-source-server-nigos
- **Spec WSQ** : https://www.fbibiospecs.cjis.gov/
- **ANSI/NIST-ITL Standard** : https://www.nist.gov/itl/iad/image-group/ansinist-itl

---

## 📞 Résumé

**Situation actuelle :**
- ✅ Images WSQ détectées correctement
- ✅ Message informatif affiché
- ⚠️ Affichage nécessite `pip install wsq` (si disponible)

**Pour afficher les images maintenant :**
```bash
# Essayer d'installer wsq
pip install wsq

# Si ça ne marche pas : utiliser NISTViewer officiel
# ou NBIS pour convertir WSQ → PNG
```

**Le code myNIST est maintenant prêt à afficher WSQ dès que la bibliothèque est disponible !**

---

**Auteur :** Yoann BAUDRIN
**Version :** 0.1.0
**Date :** 2025-01-21
