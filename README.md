# EduPaie - Gestion des paiements scolaires

Application desktop pour la gestion des paiements des élèves, développée en Python avec PySide6 et SQLite.

## Fonctionnalités

- **Gestion des élèves** : ajouter, modifier, supprimer des élèves avec recherche et filtrage par classe
- **Enregistrement des paiements** : enregistrement de paiements avec validation du solde (ne peut pas être négatif)
- **Calcul automatique du solde** : calcul en temps réel du solde restant pour chaque élève
- **Statuts de paiement** : affichage automatique du statut (Soldé / Partiellement payé / Non payé)
- **Historique des paiements** : vue chronologique de tous les paiements par élève
- **Génération de reçus** : reçus numérotés uniques exportables en PDF
- **Tableau de bord** : statistiques globales (nombre d'élèves, total encaissé, total restant dû)

## Installation

### Prérequis

- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes

1. Cloner le dépôt ou télécharger les fichiers
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Générer les données de test (optionnel) :
```bash
python generate_test_data.py
```

4. Lancer l'application :
```bash
python main.py
```

## Architecture

Le projet suit une architecture en 3 couches :

- **`models/`** : Classes de données (Élève, Paiement)
- **`repository/`** : Couche d'accès aux données (DAO) avec SQL
- **`services/`** : Logique métier (calculs, validations, règles)
- **`ui/`** : Interface utilisateur PySide6

### Schéma de la base de données

```sql
-- Table élèves
CREATE TABLE eleves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    classe TEXT NOT NULL,
    annee_scolaire TEXT NOT NULL,
    montant_du REAL NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table paiements
CREATE TABLE paiements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id INTEGER NOT NULL,
    montant REAL NOT NULL,
    date_paiement DATETIME NOT NULL,
    mode_paiement TEXT NOT NULL,
    numero_recu TEXT NOT NULL UNIQUE,
    FOREIGN KEY (eleve_id) REFERENCES eleves(id)
);
```

## Utilisation

### Enregistrer un élève

1. Aller dans l'onglet "Élèves"
2. Cliquer sur "Ajouter un élève"
3. Remplir le formulaire (nom, prénom, classe, année scolaire, montant dû)
4. Cliquer sur "Enregistrer"

### Enregistrer un paiement

1. Sélectionner un élève dans la liste
2. Cliquer sur "Enregistrer un paiement"
3. Saisir le montant, la date et le mode de paiement
4. Le système vérifie que le solde ne devient pas négatif
5. Un numéro de reçu unique est généré automatiquement

### Consulter l'historique et imprimer un reçu

1. Sélectionner un élève
2. Cliquer sur "Voir détails"
3. Dans l'historique, sélectionner un paiement
4. Cliquer sur "Voir le reçu" pour les détails ou "Imprimer le reçu (PDF)" pour générer le PDF

### Tableau de bord

L'onglet "Tableau de bord" affiche :
- Le nombre total d'élèves
- Le montant total encaissé
- Le montant total restant dû
- Le nombre d'élèves non soldés
- La liste des élèves filtrable par statut de paiement

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

## Technologies utilisées

- **Python 3.10+** : Langage principal
- **PySide6** : Interface graphique
- **SQLite** : Base de données
- **reportlab** : Génération de PDF

## Auteur

Développé dans le cadre du projet EduPaie - Gestion des paiements scolaires.
