# Documentation Technique - EduPaie

## Architecture du projet

EduPaie suit une architecture en 3 couches strictement séparées :

### 1. Couche Modèles (`models/`)

Contient les classes de données représentant les entités du domaine.

- **`Eleve`** : Représente un élève avec ses attributs (id, nom, prénom, classe, année scolaire, montant dû)
- **`Paiement`** : Représente un paiement (id, élève_id, montant, date, mode, numéro de reçu)

### 2. Couche Repository (`repository/`)

Couche d'accès aux données (DAO) qui encapsule toutes les requêtes SQL.

- **`Database`** : Singleton gérant la connexion SQLite et l'initialisation du schéma
- **`EleveRepository`** : Opérations CRUD sur les élèves (add, get_by_id, get_all, update, delete, search, filter_by_classe)
- **`PaiementRepository`** : Opérations CRUD sur les paiements (add, get_by_id, get_by_eleve, get_by_recu, get_total_by_eleve)

### 3. Couche Services (`services/`)

Logique métier : calculs, validations, règles métier.

- **`EleveService`** : Validation des données élèves, règles de suppression (vérifie les paiements)
- **`PaiementService`** : 
  - Calcul du solde (total dû - somme des paiements)
  - Détermination du statut (Soldé/Partiellement payé/Non payé)
  - Validation des paiements (montant positif, ne dépasse pas le solde)
  - Génération des numéros de reçus uniques
- **`RecuService`** : Génération de reçus PDF avec reportlab

### 4. Couche Interface (`ui/`)

Interface utilisateur PySide6, ne contient aucune logique métier ni requêtes SQL.

- **`MainWindow`** : Fenêtre principale avec onglets
- **`DashboardWidget`** : Tableau de bord avec statistiques
- **`EleveListWidget`** : Liste des élèves avec recherche et filtre
- **`EleveForm`** : Formulaire d'ajout/modification d'élève
- **`PaiementDialog`** : Dialogue d'enregistrement de paiement
- **`EleveDetailWidget`** : Détails d'un élève avec historique des paiements

## Schéma de la base de données

### Table `eleves`

| Colonne | Type | Contrainte | Description |
|---------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identifiant unique |
| nom | TEXT | NOT NULL | Nom de l'élève |
| prenom | TEXT | NOT NULL | Prénom de l'élève |
| classe | TEXT | NOT NULL | Classe de l'élève |
| annee_scolaire | TEXT | NOT NULL | Année scolaire |
| montant_du | REAL | NOT NULL | Montant total des frais |
| date_creation | DATETIME | DEFAULT CURRENT_TIMESTAMP | Date de création |

### Table `paiements`

| Colonne | Type | Contrainte | Description |
|---------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Identifiant unique |
| eleve_id | INTEGER | NOT NULL, FOREIGN KEY | Référence à l'élève |
| montant | REAL | NOT NULL | Montant du paiement |
| date_paiement | DATETIME | NOT NULL | Date du paiement |
| mode_paiement | TEXT | NOT NULL | Mode (especes/cheque/virement/mobile_money) |
| numero_recu | TEXT | NOT NULL, UNIQUE | Numéro de reçu unique |

## Choix techniques

### Python 3.10+

Langage choisi pour sa simplicité, sa large adoption et ses nombreuses bibliothèques.

### PySide6

Framework d'interface graphique moderne, officiellement supporté par Qt, offrant :
- Widgets natifs et performants
- Signal/slot pour la gestion des événements
- Support multi-plateforme (Windows, Linux, macOS)

### SQLite

Base de données légère, sans serveur, idéale pour une application desktop :
- Fichier unique facile à distribuer
- Pas de configuration serveur nécessaire
- Performantes pour les volumes de données attendus

### reportlab

Bibliothèque de génération PDF robuste et flexible :
- Contrôle total sur la mise en page
- Support des tableaux, images, styles
- Compatible avec les standards PDF

## Flux de données

### Enregistrement d'un paiement

```
UI (PaiementDialog) 
  → Service (PaiementService.create_paiement)
    → Validation (montant, solde)
    → Génération numéro reçu
    → Repository (PaiementRepository.add)
      → SQL INSERT
    → Retour paiement avec ID
  → UI affiche confirmation
```

### Calcul du solde

```
UI (EleveListWidget / DashboardWidget)
  → Service (PaiementService.get_solde)
    → Repository (EleveRepository.get_by_id)
    → Repository (PaiementRepository.get_total_by_eleve)
    → Calcul: montant_du - total_paye
  → UI affiche solde et statut
```

### Génération d'un reçu PDF

```
UI (EleveDetailWidget)
  → Service (RecuService.generer_recu_pdf)
    → Récupération données élève et paiement
    → Génération document reportlab
    → Écriture fichier PDF
  → UI affiche succès
```

## Gestion des erreurs

### Validation des entrées

- Champs obligatoires vérifiés dans les services
- Montants doivent être positifs
- Dates doivent être valides
- Messages d'erreur explicites via QMessageBox

### Exceptions SQL

- Toutes les opérations base de données sont encapsulées dans les services
- Les exceptions sont converties en ValueError avec messages explicites
- L'interface ne gère jamais directement d'exceptions SQL

### Contraintes d'intégrité

- Un élève avec des paiements ne peut pas être supprimé
- Les numéros de reçus sont uniques (contrainte UNIQUE)
- Les paiements sont liés à un élève existant (contrainte FOREIGN KEY)

## Sécurité

### Données

- Base de données SQLite locale (pas d'accès réseau)
- Pas de stockage de mots de passe
- Les reçus PDF sont générés localement

### Validation

- Toutes les entrées utilisateur sont validées
- Injection SQL impossible (utilisation de paramètres préparés)
- Les montants sont vérifiés pour éviter les dépassements

## Limites connues

1. **Pas de multi-utilisateur** : Application mono-poste, pas de gestion des droits
2. **Pas de sauvegarde automatique** : La base de données doit être sauvegardée manuellement
3. **Pas d'export Excel** : Seul l'export PDF est disponible pour les reçus
4. **Pas de gestion des années** : Les données ne sont pas archivées par année scolaire
5. **Pas de rappels de paiement** : Aucun système de notification automatique

## Améliorations possibles

1. **Authentification** : Ajouter un système de login avec rôles
2. **Sauvegarde/restauration** : Fonctionnalité de backup de la base de données
3. **Export Excel** : Exporter la liste des élèves et paiements en Excel
4. **Archivage** : Archiver les données par année scolaire
5. **Notifications** : Rappels automatiques pour les paiements en retard
6. **Statistiques avancées** : Graphiques et rapports détaillés
7. **Multi-langue** : Support de plusieurs langues
8. **Mode sombre** : Thème sombre pour l'interface

## Tests

### Données de test

Le script `generate_test_data.py` crée :
- 16 élèves répartis dans différentes classes
- 5 élèves soldés
- 5 élèves partiellement payés
- 6 élèves non payés
- Paiements variés avec différents modes de paiement

### Lancement des tests

```bash
python generate_test_data.py
```

Cela crée la base de données `edupaie.db` avec les données de test.

## Déploiement

### Packaging avec PyInstaller

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

Cela crée un exécutable autonome dans le dossier `dist/`.

### Distribution

L'application peut être distribuée avec :
- L'exécutable `.exe`
- Le fichier de base de données `edupaie.db` (avec données de test ou vide)
- Le manuel utilisateur `MANUEL_UTILISATEUR.md`

L'utilisateur n'a besoin d'aucune installation de Python ou de dépendances.
