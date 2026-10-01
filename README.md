# EduPaie — Gestion des paiements scolaires

Application desktop de gestion des paiements de scolarité (monnaie : **FCFA**), développée en **Python / PySide6** avec **SQLite** et génération de **reçus PDF** (reportlab).

![Statuts](https://img.shields.io/badge/statuts-Sold%C3%A9%20%2F%20Partiel%20%2F%20Non%20pay%C3%A9-2c5282)

## Fonctionnalités

- **Gestion des élèves** : ajout, modification, suppression (avec garde-fou : impossible s'il existe des paiements) ; matricule généré automatiquement ; liste **recherchable** (nom, prénom, matricule) et **filtrable** par classe **et** par statut.
- **Gestion des classes** : page dédiée pour créer, modifier et supprimer les classes et leurs **frais de scolarité FCFA** (suppression refusée si des élèves y sont inscrits) ; modifier les frais recalcule automatiquement les soldes de tous les élèves de la classe.
- **Enregistrement des paiements** : montant, date, mode (espèces / chèque / virement / mobile money), référence optionnelle ; **le solde ne peut jamais devenir négatif** — un avertissement temps réel signale tout montant supérieur au solde restant.
- **Calcul automatique du solde** : solde = total dû (plans de frais par classe) − somme des paiements valides ; **statut dérivé** (Soldé / Partiellement payé / Non payé) affiché dans la liste et la fiche élève.
- **Historique des paiements** : liste chronologique par élève avec **solde après chaque paiement**, paiements annulés visibles et distingués.
- **Reçus** : numéro unique `REC-AAAA-NNNNNN` généré **atomiquement**, snapshot figé en base → **téléchargement PDF** et **réimpression strictement identique**, aperçu avant impression, impression directe via la visionneuse système.
- **Annulation de paiement** (motif obligatoire) : historique conservé, soldes recalculés.
- **Modification et suppression des paiements** : corriger un montant/date/mode (le numéro de reçu est conservé, le snapshot est régénéré) ou supprimer définitivement une saisie erronée — toujours avec validation du solde.
- **Tableau de bord** : nombre d'élèves, total encaissé, total restant dû, élèves non soldés, répartition par statut et liste filtrable.
- **Classes** : de la 6ème à la Terminale, séries A et D (14 classes par défaut, montants FCFA par classe).
- **Interface responsive** : barre latérale repliable (auto sous 950 px), barres de filtres et d'actions qui se réorganisent en plusieurs lignes selon la largeur de la fenêtre.
- **Robustesse** : argent stocké en **entiers (centimes)** — pas d'erreurs d'arrondi ; transactions SQLite explicites ; schéma auto-migré au démarrage.

## Démarrage rapide

```bash
pip install -r requirements.txt
python main.py                 # lance l'application
python generate_test_data.py   # (optionnel) 15 élèves de démonstration
python data/seed.py            # (optionnel) régénère la DB embarquée
```

Au premier lancement, la base est créée dans `%APPDATA%/EduPaie` (Windows) ou `~/.config/EduPaie` (Linux/macOS), avec classes et plans de frais par défaut. Les reçus PDF sont enregistrés dans `~/Documents/EduPaie/Recus`.

> Astuce : la variable d'environnement `EDUPAIE_DB` permet de pointer vers une autre base (utilisé par les tests).

## Architecture (3 couches)

```
app/
├── config.py               # Chemins (APPDATA/_MEIPASS), monnaie, école
├── models/                 # Student, Payment, ClassModel, SchoolYear
├── data/
│   ├── db.py               # Singleton SQLite : FK, WAL, transactions, migrations
│   ├── schema.sql          # Schéma idempotent + données de base
│   └── repositories/       # Accès données (SQL uniquement)
├── services/               # Logique métier et validations
│   ├── student_service.py  # CRUD élèves, matricules, année courante
│   ├── payment_service.py  # Paiements atomiques, snapshots, statistiques
│   ├── balance_service.py  # Soldes et statuts
│   └── receipt_service.py  # Reçus PDF depuis le snapshot figé
├── services/               # Logique métier et validations
│   ├── student_service.py  # CRUD élèves, matricules, année courante
│   ├── payment_service.py  # Paiements atomiques, snapshots, statistiques
│   ├── class_service.py    # CRUD classes + plans de frais
│   ├── balance_service.py  # Soldes et statuts
│   └── receipt_service.py  # Reçus PDF depuis le snapshot figé
main.py                     # Point d'entrée (logging, DB, thème, excepthook)
tests/test_services.py      # Tests pytest (base isolée)
build.py                    # Packaging PyInstaller
```

Règles clés :
- **Atomicité** : compteur de reçus + paiement + snapshot écrits dans **une seule transaction** (pas de doublon de numéro possible).
- **Snapshot figé** : le PDF est régénéré depuis les données enregistrées à l'émission — les modifications ultérieures de l'élève ne dénaturent jamais un reçu.
- **Suppression protégée** : un élève avec paiements ne peut pas être supprimé (préservation des reçus émis).

## Utilisation

### Enregistrer un paiement
1. Onglet **Élèves** → sélectionner un élève → **Enregistrer un paiement**
2. Saisir le montant (un aperçu affiche le solde après paiement ; tout dépassement est refusé), la date, le mode
3. Le reçu est généré automatiquement avec son numéro unique — disponible immédiatement dans la **fiche élève**

### Consulter / télécharger / imprimer un reçu
1. **Élèves** → double-clic (ou **Voir la fiche**)
2. Sélectionner un paiement dans l'historique → **Voir le reçu**, **Télécharger le reçu (PDF)** ou **Imprimer le reçu**

### Tableau de bord
L'onglet **Tableau de bord** affiche les cartes (élèves, encaissé, restant dû, non soldés), la répartition Soldés / Partiels / Non payés et la liste filtrable par statut (double-clic = ouvrir la fiche).

## Tests

```bash
python -m pytest tests/ -v
```

16 tests couvrent : CRUD élèves, matricules dupliqués, validations (nom, montants, dates, modes), statuts (non payé → partiel → soldé), dépassement de solde refusé, annulation avec restauration du solde, séquence de numéros de reçus, immutabilité des snapshots, génération PDF.

## Packaging (Windows)

```bash
python build.py    # produit dist/EduPaie.exe (DB seed et schéma embarqués)
```

## Auteur

Projet pédagogique EduPaie — gestion des paiements scolaires.
