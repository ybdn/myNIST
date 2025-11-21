# Conception hub d'accueil (Phase 0)

Issue GitHub #1 — cadrage UX de l'écran d'accueil du hub des modes (Visualiser/Éditer, Comparer, Exporter PDF). Livrable attendu : wireframes textuels + décisions de navigation et de persistance.

## 1. Objectifs et périmètre
- Offrir dès le lancement un choix explicite entre les 3 modes sans passer par les menus.
- Mettre en avant le fichier courant et les derniers fichiers utilisés pour réduire le temps d'accès.
- Préparer la navigation globale (retour au hub, passage d'un mode à l'autre) sans casser le 3-panneaux existant.

## 2. Principes UX
- Action en 1 clic ou 1 raccourci (cartes cliquables, touche Entrée sur la sélection, glisser-déposer).
- Lisibilité claire : intitulé + sous-texte sur chaque carte, zero jargon.
- Feedback d'état : bannière « fichier en cours » quand un NIST est déjà chargé ; message explicite en cas de fichier manquant dans la liste des récents.
- Robustesse offline : aucune dépendance réseau, persistance simple en local.

## 3. Wireframes textuels

### 3.1 Accueil (aucun fichier chargé)
```text
+--------------------------------------------------------------+
| myNIST                                        Ouvrir… (bouton)|
|--------------------------------------------------------------|
|  Que voulez-vous faire ?                                     |
|                                                              |
|  [ Visualiser / Éditer ]  [ Comparer ]  [ Exporter relevé PDF]|
|  (icône + 2 lignes de contexte sous chaque carte)            |
|                                                              |
|  ┌--------------------------------------------------------┐  |
|  | Glissez un fichier .nist/.eft/.an2 ici pour ouvrir     |  |
|  └--------------------------------------------------------┘  |
|--------------------------------------------------------------|
|  Derniers fichiers (max 6)                                  |
|  1) UK/29722916D~CO912...nist   21/01  Type 2/14   [Ouvrir]  |
|  2) HR/12883247_3190184.nist    20/01  Type 2/4/9/14 [Ouvrir]|
|  ...                                                         |
|  [Parcourir…]  [Vider la liste]                              |
|--------------------------------------------------------------|
|  Raccourcis : Ctrl+O Ouvrir · Ctrl+E Export Signa · F1 Aide  |
+--------------------------------------------------------------+
```
- Cartes cliquables + focus clavier (flèches + Entrée). Un clic ouvre le sélecteur de fichier si rien n'est chargé, ou bascule sur le mode si un fichier est déjà présent.
- La zone d'import accepte drag & drop (reprise du comportement actuel).
- Les récents affichent nom, chemin, types détectés (si disponibles), date d'ouverture. Bouton « Ouvrir » relance directement le fichier.

### 3.2 Accueil avec fichier déjà chargé
```text
+--------------------------------------------------------------+
| Fichier en cours : TEST.efts   (Viewer)    [Reprendre]       |
|--------------------------------------------------------------|
|  Reprendre ou changer de mode ?                              |
|                                                              |
|  [ Continuer à visualiser ] [ Comparer ] [ Exporter relevé ] |
|    (mentionne fichier courant)                               |
|                                                              |
|  Derniers fichiers (le courant en premier, puis historiques) |
|  1) TEST.efts   Aujourd'hui   Type 2/4/10/14  [Reprendre]    |
|  2) UK/2972...  21/01         Type 2/14       [Ouvrir]       |
|  ...                                                         |
|--------------------------------------------------------------|
|  Lien retour : « Aller au hub » accessible depuis chaque mode|
+--------------------------------------------------------------+
```
- Le bouton « Reprendre » renvoie au mode actif précédent (Viewer/Comparaison/Export PDF).
- Si le fichier courant a disparu, un message s'affiche et l'entrée est grisée avec option de suppression.

## 4. Navigation et état global
- Routeur recommandé : `QStackedWidget` dans `MainWindow`, avec 4 vues : `HomeView` (hub), `ViewerView` (3 panneaux existants), `ComparisonView`, `PdfExportView`.
- Transitions :
  - Démarrage → `HomeView`.
  - Carte « Visualiser/Éditer » ou double-clic sur un récent → ouvre/charge le fichier puis `ViewerView`.
  - Carte « Comparer » → `ComparisonView` ; si aucun fichier fourni, ouvrir un dialogue double-sélection.
  - Carte « Exporter relevé PDF » → `PdfExportView` ; si aucun fichier, demander un fichier d'entrée.
  - Bouton « Aller au hub » dans chaque vue pour revenir à `HomeView` sans détruire l'état du fichier courant.
- Raccourcis : `Alt+1` Hub, `Alt+2` Viewer, `Alt+3` Comparaison, `Alt+4` Export PDF (en plus des raccourcis existants pour ouvrir/exporter).
- Barre d'état globale : affiche mode actif + nom du fichier courant (si présent).

## 5. Récents : persistance et règles
- Stockage local JSON : `~/.config/mynist/recent_files.json` (structure : liste ordonnée `{path, opened_at, last_mode, summary_types}`).
- Cap sur 8 entrées ; dédup (un chemin unique), entrée supprimée si le fichier n'existe plus.
- Mise à jour quand : fichier ouvert via hub, drag & drop, menu Fichier > Ouvrir.
- Affichage : nom court + chemin répertoire, date relative (Aujourd'hui/Hier/ ) + types détectés si déjà parsés.
- Actions : « Vider la liste » (supprime le JSON), [Ouvrir], [Révéler dans le dossier].

## 6. Textes, boutons, icônes
- Cartes :
  - `Visualiser / Éditer` — sous-texte « Parcours 3 panneaux, inspection et édition Type-2 » — icône œil/stylo.
  - `Comparer` — sous-texte « Cote à cote, points, recalage DPI » — icône double-écran.
  - `Exporter relevé PDF` — sous-texte « Décadactylaire A4, métadonnées Type-1/2 » — icône PDF/feuille.
- Boutons : `Ouvrir…`, `Parcourir…`, `Vider la liste`, `Reprendre`, `Aller au hub` (depuis autres vues).
- Étiquettes : `Derniers fichiers`, `Fichier en cours`, `Glissez un fichier ici`.
- Réemploi d'icônes : conserver le plus (ouvrir) et stop (fermer) existants ; ajouter jeux simples (pdf, compare, home) dans `mynist/resources/icons/`.

## 7. Critères d'acceptation
- Au lancement, l'écran hub s'affiche avec les 3 cartes et la zone de dépôt.
- Un fichier peut être ouvert via : carte « Visualiser/Éditer », bouton « Ouvrir… », drag & drop, clic sur un récent.
- Les récents se mettent à jour et persistent entre sessions ; un fichier manquant est signalé sans crash.
- Depuis n'importe quel mode, retour au hub en 1 clic ou `Alt+1` ; bascule vers un autre mode conserve le fichier chargé.
- L'état global (mode actif + fichier courant) est visible en haut ou dans la barre d'état.
- Textes FR lisibles, sans jargon ; actions accessibles au clavier.

## 8. Prochaines étapes d'implémentation
1) Créer `HomeView` (QWidget) avec cartes, zone drop, liste récents ; brancher `QStackedWidget` dans `MainWindow`.
2) Facteur commun « état global » : un petit contrôleur/objet partagé (fichier courant, derniers fichiers, mode actif).
3) Ajouter service de persistance pour les récents (lecture/écriture JSON + validations).
4) Ajouter boutons « Aller au hub » / « Reprendre » dans Viewer/Comparaison/Export PDF.
5) Ajouter icônes manquants dans `mynist/resources/icons/` + styles légers (couleurs différenciées par mode).
