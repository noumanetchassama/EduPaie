# EduPaie - Gestion des paiements scolaires

Application desktop pour la gestion des paiements des élèves, développée en Python avec PySide6 et SQLite.

## Fonctionnalités

- Gestion des élèves (ajouter, modifier, supprimer)
- Enregistrement des paiements avec validation du solde
- Calcul automatique du solde restant
- Historique des paiements par élève
- Génération de reçus numérotés (PDF/impression)
- Tableau de bord avec statistiques

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Architecture

- `models/` : Classes de données (Élève, Paiement)
- `repository/` : Accès aux données (DAO)
- `services/` : Logique métier
- `ui/` : Interface PySide6

## Branches de développement

- `feature/gestion-eleves` : CRUD élèves
- `feature/enregistrement-paiements` : Enregistrement paiements
- `feature/calcul-solde` : Calcul solde et statuts
- `feature/historique-paiements` : Historique et reçus
- `feature/generation-recus` : Génération PDF reçus
- `feature/tableau-bord` : Tableau de bord
- `feature/jeu-donnees-test` : Données de test
- `documentation` : Documentation
- `packaging` : Packaging PyInstaller
