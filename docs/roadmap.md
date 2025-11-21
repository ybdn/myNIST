# Roadmap myNIST

Document de référence pour l'évolution de myNIST : couverture des nouveaux types NIST, édition, export PDF, comparaison, et ajout d'une page d'accueil orientée modes d'usage.

## 0. Vision et principes

- Offrir trois parcours clairs dès l'accueil : **Visualiser/Éditer**, **Comparer**, **Exporter PDF**.
- Rester 100 % local (pas de backend), architecture MVC actuelle conservée.
- Sécurité et intégrité des fichiers source : les exports créent toujours un nouveau fichier.
- Tests systématiques (unitaires, pytest-qt, vérifications visuelles sur fixtures).

## 1. Page d'accueil (hub des modes)

- Écran d'accueil avant la fenêtre 3 panneaux : cartes/actions "Visualiser/Éditer un NIST", "Comparer", "Exporter relevé PDF".
- Bloc "Derniers fichiers" (accès rapide) et bouton "Ouvrir un NIST".
- Gestion d'état global (fichier courant, historique) + navigation retour au hub.
- Implémentation suggérée : QWidget dédié + stack de vues (QStackedWidget) ou routeur léger dans `MainWindow`.

## 2. Phase Fonctionnelle

### Phase 1 — Socle et types supplémentaires (1/4/7/10)

- Parsing/affichage fiables des records Type-1, Type-4, Type-7, Type-10 (et existants 13/14/15…)
- Améliorer libellés dans l'arborescence (`RECORD_TYPE_NAMES`) et métadonnées visibles (IDC, position, impression type).
- ImagePanel : meilleure détection formats (JPEG/PNG/WSQ, futur JPEG2000), rotation/EXIF, fallback explicites.
- Tests : fixtures couvrant ces types, vérification extraction champs et affichage image.

### Phase 2 — Édition Type-2 + sauvegarde/export

- Rendre le tableau Type-2 éditable (double-clic) avec validation par format (dates, numériques, texte).
- Ajouter/supprimer des champs (entrer numéro + valeur), marquer l'état "modifié", bouton "Enregistrer" / "Exporter sous…".
- Annulation minimale (undo dernier changement) et confirmation avant discard.
- Tests pytest-qt sur édition, sauvegarde, règles de validation.

### Phase 3 — Export relevé décadactylaire PDF

- Contrôleur PDF dédié : map Type-4/14 (ou Type-10 si 10-print disponible) vers un gabarit A4.
- Conversion WSQ→raster, options DPI/nb-couleur, insertion métadonnées Type-1/2 (TCN, ORI, date, nom sujet).
- Choix techno : QPdfWriter ou ReportLab; gabarit paramétrable.
- Tests visuels sur fixtures, comparaison dimensions/presence des 10 doigts.

### Phase 4 — Comparaison & annotations

- Vue comparer (split) acceptant : NIST vs NIST, image/PDF rasterisée vs NIST.
- Placement de points sur chaque image, compteur, undo/reset, visibilité par couche.
- Export capture JPG du cote-à-cote avec points (screenshot programmatique).
- **Resample/Calibrate** : outils pour recaler et rescaler les deux vues (alignement DPI/échelle, translation) afin de superposer visuellement des empreintes de sources différentes avant annotation.
- Navigation rapide par doigt/IDC, zoom/pan synchronisés si possible.
- Tests d'interaction (pytest-qt) sur ajout/suppression de points et export.

### Phase 5 — Intégration navigation & accueil

- Routeur/vues : bascule Accueil ↔ Viewer ↔ Comparaison ↔ Export PDF sans recharger l'appli.
- Affichage d'état global (fichier chargé, mode actif) et gestion des fichiers récents (persistés).
- Points d'entrée depuis menus/toolbar vers chaque mode.

### Phase 6 — Robustesse, perf, distribution

- Tests de régression automatisés (fixtures multi-types, export PDF, comparaison).
- Vérif perf mémoire pour gros NIST et images haute résolution; messages d'erreur clairs.
- Mise à jour docs utilisateur/dev, notes de version; build PyInstaller.

## 3. Plan d'exécution synthétique

1. **Cadrage UX** : wireframe page d'accueil + flows des 3 modes, choisir les options PDF/comparaison.
2. **Phase 1** (socle types) → **Phase 5** (navigation/hub) pour installer le cadre.
3. **Phase 2** (édition Type-2) puis **Phase 4** (comparaison) selon priorité métier.
4. **Phase 3** (PDF décadactylaire) une fois les données fiables et images maîtrisées.
5. **Phase 6** (stabilisation) avant livraison.

## 4. Dépendances et risques

- Décodeurs image : WSQ (module `wsq` ou NBIS), éventuel support JPEG2000 si présent dans les fichiers.
- Qualité des fixtures nécessaires pour valider Type-1/4/7/10, PDF, comparaison.
- Ergonomie édition : éviter les erreurs silencieuses, besoin de validation stricte pour les champs critiques.

## 5. Livrables par phase

- Code + tests + fixtures + doc (README + docs/dev + aide utilisateur), captures d'écran pour accueil/comparaison/PDF.
- Binaire PyInstaller mis à jour après phase 6.

## 6. Issues GitHub à créer (proposition)

- Phase 0 – Conception hub d'accueil : maquettage (wireframes) + parcours utilisateur (3 modes) + critères d'acceptation.
- Phase 1 – Support complet Types 1/4/7/10 : parsing, labels arborescence, métadonnées visibles, détection formats image (incl. WSQ/JPEG/PNG), rotation/EXIF.
- Phase 1 – Fixtures multi-types : collecter/ajouter jeux de tests couvrant 1/2/4/7/10/13/14/15 + images WSQ/JPEG.
- Phase 1 – Gestion des fichiers tronqués : afficher erreur claire et permettre (optionnel) une ouverture partielle; couvrir les 2 fichiers Interpol tronqués.
- Phase 2 – Tableau Type-2 éditable : rendre la grille éditable, validations (date/numérique/texte), annulation simple, état "modifié".
- Phase 2 – Ajout/Suppression champs Type-2 : UX d'ajout par numéro/valeur, suppression, confirmations, tests pytest-qt.
- Phase 3 – Export PDF décadactylaire : contrôleur PDF, gabarit A4, mapping doigts, insertion métadonnées, options DPI/nb-couleur, conversion WSQ→raster.
- Phase 3 – Gabarit PDF & tests visuels : définir le template, inclure exemples et scripts de comparaison visuelle (tolérance dimensions/résolution).
- Phase 4 – Vue Comparaison : écran split, zoom/pan, chargement NIST/NIST ou image/PDF rasterisé, navigation doigt/IDC.
- Phase 4 – Annotation points & export : couches de points, compteur, undo/reset, export capture JPG cote-à-cote.
- Phase 4 – Resample/Calibrate en comparaison : alignement échelle/DPI + translation pour recaler les deux images avant annotation; bouton de réinitialisation.
- Phase 5 – Navigation/routeur : QStackedWidget ou équivalent, transitions Accueil ↔ Viewer ↔ Comparaison ↔ Export PDF, gestion fichiers récents/état global.
- Phase 6 – Campagne régression : pack de tests automatiques (pytest/pytest-qt), scénarios de charge (gros NIST), vérif mémoire et messages d'erreur.

## 7. Jeux d'essai fournis (nist-files/) et couverture attendue

- **Panel Type-4/14/15** : `HR/12883247_3190184.nist`, `HU/LakatosLaszlo.nst`, `LT/LTT*.nst`, `NL/313400449975.nist`, `PT/07150440-...n ist`, `TR/000000df H.int`, `USA/EID3641944165 USA.efts`, `USA/TEST efts.nist`, série `NIST DIFFICILES PN/*` (Type-14 multiples), `UK/29722916D~CO91210210665J.nst`.
- **Type-7** : `TR/000000df H.int`, `TR/000000df H.A..int` (vérifier rendu image user-defined + fallback texte).
- **Type-10 (faces/SMT)** : `Interpol/FRA-24000000448327A (FI).nist`, `TR/000000df H.int`, `TR/000000df H.A..int`.
- **Type-9 (minuties)** : `HR/12883247_3190184.nist`, `PT/07150440-JPT200001911-3174519-34528_e780a375d06a.nist` (prévoir affichage/indication présence minuties, même si non visualisées).
- **Fichiers tronqués** : `Interpol/FABLStemp8865791272998619994.NST-neu.nst`, `Interpol/NIST File (INTERPOL V5.03) - 730020_06N.nst` (attente : message compréhensible + log; pas de crash).
- **Exports Signa existants** : `102556281*` et `109018515*` (base et double export) pour tests régression sur Type-2 et Type-14/15.
- **Interop .efts / .int** : `USA/EID3641944165 USA.efts`, `USA/TEST efts.nist`, `TR/*.int` pour valider extensions variées.

Attendus QA :

- Ouvrir sans crash l’ensemble des fichiers valides (47/49) et afficher au moins la structure 1/2/4/10/14/15 quand présents.
- Message clair pour les 2 fichiers tronqués; l’utilisateur comprend qu’ils sont incomplets.
- Vérifier rendu image Type-7/10 et WSQ (si dépendance dispo) sur les fichiers listés.
- Vérifier affichage Type-15 (palm) sur `102556281*`, `109018515*`, `HR/12883247*`, `PAYS BASQUE/20200821-59496422.nst`, `PT/...`, `UK/...`.

## 8. Organisation cible du repo / refactor léger

- **Vues** : `mynist/views/home_view.py` (hub/accueil), `mynist/views/comparison_view.py` (split, zoom/pan, resample/calibrate, annotations), `mynist/views/pdf_preview_view.py` (optionnel) ; conserver `main_window` comme routeur (QStackedWidget ou équivalent).
- **Contrôleurs** : `controllers/pdf_controller.py` (relevé décadactylaire), `controllers/comparison_controller.py` (chargement double source, recalage, export capture), `controllers/file_controller.py` inchangé, `controllers/export_controller.py` pour Signa.
- **Tests/fixtures** : sous-dossiers `tests/fixtures/type4`, `type7`, `type10`, `palm15`, `efts_int`, `tronques` avec un échantillon réduit issu de `nist-files/`. Conserver `nist-files/` comme banque manuelle.
- **Ressources** : regrouper icônes/emojis/styles dans `mynist/resources/`; prévoir thèmes pour accueil/comparaison.
- **Docs** : roadmap unique (ce fichier), README renvoyant vers roadmap; index doc déjà mis à jour.

## 9. Technologies et dépendances à prévoir

- **Parsing NIST** : `nistitl` (existant); dépendance optionnelle `wsq` (Pillow plugin) ou NBIS `dwsq` pour WSQ; garder messages explicites en absence.
- **GUI Qt** : PyQt5 (existant). Navigation par QStackedWidget. Comparaison/annotations via QGraphicsView/Scene (zoom/pan, couches de points, resample/calibrate = transformation affine + reset).
- **Images** : Pillow (existant) ; support JPEG2000 si nécessaire via `imagecodecs` ou `glymur` (optionnel) ; EXIF/rotation sur JPEG/PNG.
- **PDF** : ReportLab conseillé pour le relevé décadactylaire (gabarit A4, unités physiques) ; alternative Qt QPdfWriter. Rasterisation PDF (pour comparaison) possible via `PyMuPDF` (`fitz`) ou `pdf2image` + poppler.
- **Tests** : `pytest`, `pytest-qt` (existant), option `pytest-cov` pour couverture; tests “oracle” dimensionnels plutôt que pixel-perfect pour images/PDF.
- **Build** : PyInstaller (existant) ; option `pip-tools` ou `python -m build` pour gérer/verrouiller les deps.

## 10. Actions immédiates proposées

1. Sélectionner un sous-ensemble de `nist-files/` à copier en `tests/fixtures/` (un par type/famille + les 2 tronqués).
2. Créer les issues listées (sections 6 et resample/calibrate) + ajouter l’issue “ajout dépendances optionnelles” (wsq/JPEG2000/ReportLab/PyMuPDF).
3. Mettre à jour `requirements.txt`/`README` avec les dépendances optionnelles (WSQ, PDF) et leurs usages.
4. Sketcher le hub (home_view) et la vue comparaison (points + resample/calibrate) avant dev.
