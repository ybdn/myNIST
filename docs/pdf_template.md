# Gabarit PDF décadactylaire

Organisation utilisée (A4, 300 DPI) :
- Main gauche : P, I, M, A, O (colonne gauche).
- Main droite : P, I, M, A, O (colonne droite).
- Simultanés : main gauche, pouces, main droite.
- Paumes : gauche, droite.
- Extras (images non mappées) : bandeau final (3 images max).

Métadonnées affichées : TCN, ORI, Date, Nom (issus du Type-2 quand disponibles).

Formats d’image pris en charge : JPEG/PNG/BMP, JPEG2000 (via Pillow si plugin), WSQ (si `dwsq` NBIS est présent). Sans `dwsq`, les WSQ sont ignorées dans le PDF et un message indique l’absence de décodeur.

Exécution :
- Depuis le hub : carte “Exporter PDF” ouvre la vue export dédiée.
- Menu Fichier ou Navigation (Alt+4) : ouvre la même vue. Bouton “Exporter le PDF” lance la génération.

Tests :
- `tests/test_pdf_controller.py` vérifie la génération d’un PDF à partir d’un fixture.
- `tests/test_pdf_dimensions.py` contrôle la structure (1 page, dimensions A4 approchantes) sur plusieurs fixtures.
- `tests/test_image_tools.py` couvre la détection de formats.

Limitations :
- Si le fichier ne contient que des WSQ et que `dwsq` n’est pas disponible, le PDF sera vide ; installez NBIS/dwsq pour inclure les empreintes WSQ.
