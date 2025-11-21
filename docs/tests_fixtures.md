# Fixtures de tests myNIST (Phase 1)

Sous-ensemble léger de `nist-files/` copié dans `tests/fixtures/` pour rendre `pytest` autonome.

## Inventaire
- `type4/HR_12883247_3190184.nist` — Types 2/4/9/15 (empreinte + minuties) — couvre Type-4 et Type-9.
- `type7/TR_000000df_H.int` — Types 2/4/7/10 (user-defined image) — couvre Type-7.
- `type10/TR_000000df_H.int` — idem, utilisé pour tests Type-10 (face/SMT).
- `type10/Interpol_FRA_24000000448327A_FI.nist` — Type-10 léger (PNG), pour tests image rapides.
- `type9/HR_12883247_3190184.nist` — réutilise le fichier HR pour validateur Type-9.
- `palm15/109018515_export_test.nist` — Types 2/14/15 (palm).
- `efts_int/USA_TEST_efts.nist` — fichier EFTS (Types 2/4).
- `efts_int/TR_000000df_H.int` — fichier .int (Types 2/4/7/10).
- `signa/102556281_export_test.nist` — Export Signa Multiple (Types 2/14/15).
- `signa/109018515_export_test.nist` — Export Signa Multiple (Types 2/14/15).
- `tronques/Interpol_FABLStemp8865791272998619994.NST-neu.nst` — fichier tronqué (doit échouer proprement).
- `tronques/Interpol_NIST_File_INTERPOL_V5.03_-_730020_06N.nst` — fichier tronqué (doit échouer proprement).

## Usage
- Les tests d’intégration chargent ces fichiers via `tests/test_fixture_parsing.py`.
- Aucune dépendance au dossier `nist-files/` n’est requise pour exécuter `pytest`.
- Les fichiers tronqués sont attendus en échec (`parse()` retourne False) pour vérifier les messages d’erreur non bloquants.
