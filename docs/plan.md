Plan d'implémentation myNIST - Visualiseur NIST avec Export Signa Multiple
Pile technologique retenue
Bibliothèque NIST : nistitl (Idemia) - parsing ANSI/NIST-ITL
GUI Framework : PyQt5 - interface moderne pour Ubuntu
Packaging : PyInstaller - exécutable unique
Architecture : MVC (Model-View-Controller)
Étapes d'implémentation

1. Configuration initiale du projet
   Créer la structure de répertoires (mynist/, models/, views/, controllers/, utils/, resources/)
   Créer requirements.txt (nistitl, PyQt5, Pillow)
   Créer setup.py pour l'installation du package
   Créer .gitignore (dist/, pycache, \*.pyc, etc.)
2. Modèle de données NIST (models/)
   nist_file.py : Classe NISTFile pour charger et parser les fichiers .nist avec nistitl
   record.py : Classes pour représenter les différents types de records (Type-2, fingerprints)
   field.py : Gestion des champs NIST (dont 2.215 et 2.217)
3. Interface graphique à 3 panneaux (views/)
   main_window.py : Fenêtre principale avec QSplitter horizontal
   Panel 1 (file_panel.py) : Arborescence des records du NIST (QTreeWidget)
   Panel 2 (data_panel.py) : Affichage des champs alphanumériques Type-2 (QTableWidget)
   Panel 3 (image_panel.py) : Affichage des images d'empreintes (QLabel avec QPixmap)
   Menu "File" : Open NIST, Export Signa Multiple, Quit
   Menu "Help" : About
4. Contrôleurs (controllers/)
   file_controller.py : Ouverture/lecture fichiers NIST
   parser_controller.py : Logique de parsing avec nistitl
   export_controller.py : Export "Signa Multiple" (règle fixe : supprimer 2.215, 2.217 = "11707")
   image_controller.py : Extraction et affichage des images d'empreintes
5. Fonctionnalité "Export Signa Multiple"
   Implémenter la logique de modification :
   Charger le NIST source
   Supprimer le champ 2.215 du record Type-2
   Remplacer le contenu du champ 2.217 par "11707"
   Exporter le nouveau fichier NIST
   Interface : bouton/menu déclenchant un QFileDialog pour sauvegarder
6. Utilitaires (utils/)
   config.py : Configuration de l'application
   logger.py : Système de logging
   constants.py : Constantes (types NIST, noms de champs)
7. Point d'entrée (mynist/main.py)
   Initialisation QApplication
   Lancement de la fenêtre principale
   Gestion des arguments en ligne de commande (optionnel)
8. Configuration PyInstaller
   Créer mynist.spec
   Configurer les imports cachés (nistitl, PyQt5.sip)
   Inclure les ressources (icons, styles)
   Mode --onefile pour un exécutable unique
   Tester le build sur Ubuntu
9. Tests et validation
   Tester avec des fichiers NIST réels
   Vérifier l'affichage des 3 types de contenus
   Tester l'export "Signa Multiple"
   Builder avec PyInstaller et tester l'exécutable
   Livrables
   ✅ Application myNIST fonctionnelle avec GUI PyQt5
   ✅ Visualisation 3 panneaux (arbre records, champs, images)
   ✅ Export "Signa Multiple" avec règles fixes
   ✅ Exécutable unique Ubuntu (via PyInstaller)
   ✅ Code organisé en architecture MVC Prêt à démarrer l'implémentation ?
