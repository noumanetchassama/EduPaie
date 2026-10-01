# Documentation technique — EduPaie

## 1. Vue d'ensemble

EduPaie est une application desktop **Python 3.10+ / PySide6** (architecture MVC 3 couches) avec **SQLite** et génération de reçus PDF via **reportlab**.

```
┌────────────────────────────────────────────────────────┐
│ UI (app/ui)                                            │
│   main_window (navigation latérale + QStackedWidget)   │
│   dashboard_page │ students_page │ dialogs │ widgets   │
├────────────────────────────────────────────────────────┤
│ Services (app/services)  — logique métier              │
│   student_service │ payment_service │ balance_service  │
│   receipt_service │ exceptions                         │
├────────────────────────────────────────────────────────┤
│ Data (app/data) — accès données                        │
│   db.py (singleton, FK/WAL/transactions)               │
│   repositories/ (SQL pur) │ schema.sql │ migrations    │
├────────────────────────────────────────────────────────┤
│ SQLite (APPDATA ou EDUPAIE_DB)                         │
└────────────────────────────────────────────────────────┘
```

Les couches communiquent par modèles (`app/models`) : `Student`, `Payment`, `ClassModel`, `SchoolYear`. Les exceptions métier (`ValidationError`, `BusinessRuleError`, `NotFoundError`, `DatabaseError`) sont levées par les services et converties en messages par l'UI.

## 2. Modèle de données

| Table | Rôle | Points clés |
|---|---|---|
| `school_year` | Années scolaires | `is_current` unique en pratique |
| `class` | Classes | uniques par (nom, année) |
| `student` | Élèves | `matricule` UNIQUE, FK classe, `is_active` |
| `fee_plan` | Frais dus par classe/année | `amount_int` en **centimes** |
| `payment` | Paiements | `amount_int` centimes, `receipt_no` UNIQUE, statut `valide`/`annule` |
| `receipt_snapshot` | Reçu figé (JSON) | 1:1 avec payment, source du PDF |
| `receipt_counter` | Compteur par année | numérotation `REC-AAAA-NNNNNN` |

**Argent = entiers (FCFA, pas de sous-unité)** partout — pas d'erreurs d'arrondi. Formatage à l'affichage : `app.config.format_euros` (ex. `586 000 FCFA`). Les bases créées en « centimes d'euro » avant la v2 sont converties automatiquement au démarrage (×100, flag `fcfa_v2` en table `meta`).

Le schéma (`app/data/schema.sql`) est **idempotent** et insère les données de base (année courante, classes et plans de frais par défaut, compteurs). `Database.initialize_schema()` l'exécute à **chaque démarrage** et applique une **migration légère** (colonnes manquantes sur bases anciennes).

## 3. Règles métier

### 3.1 Solde et statut
```
total_dû      = SUM(fee_plan.amount_int) de la classe de l'élève (année courante)
total_payé    = SUM(payment.amount_int) WHERE status='valide'
solde         = total_dû − total_payé      # jamais < 0 après un paiement
statut        = Soldé si solde == 0
                Partiellement payé si 0 < total_payé < total_dû
                Non payé sinon
```
(`BalanceService.is_overdue` signale en complément les échéances dépassées.)

### 3.2 Validation d'un paiement (`PaymentService.create_payment`)
1. Élève existant, année courante résolue.
2. Montant > 0 (accepte `250,00`), mode ∈ {especes, cheque, virement, mobile_money}.
3. Date ≤ aujourd'hui (format `YYYY-MM-DD`).
4. **`montant ≤ solde`** sinon `BusinessRuleError` — le solde ne peut pas devenir négatif. (`allow_overpayment` existe pour un usage explicite et volontaire.)
5. Insertion **atomique** (voir 3.3).

### 3.3 Numérotation et snapshot atomiques
`_insert_payment_atomic` exécute dans **une seule transaction SQLite** :
1. `UPDATE receipt_counter SET last_number = last_number + 1 WHERE year = ?` (créé si absent) ;
2. `INSERT INTO payment` avec `receipt_no = REC-AAAA-%06d` (contrainte UNIQUE en filet de sécurité) ;
3. `INSERT INTO receipt_snapshot` avec le JSON figé (école, élève, classe, montants avant/après, mode, date d'émission).

Un échec quelconque annule tout (rollback) : jamais de paiement sans numéro ni de numéro consommé sans paiement.

### 3.4 Ré-impression identique
`ReceiptService` génère le PDF **depuis le snapshot** (jamais depuis les données courantes) : modifier un élève ou les tarifs ne dénature pas un reçu émis. Export vers `~/Documents/EduPaie/Recus/` (ou chemin choisi), ouverture système pour impression directe.

### 3.5 Suppression protégée
`StudentService.delete_student` refuse la suppression d'un élève ayant des paiements (`BusinessRuleError`) — les reçus émis doivent rester traçables. L'annulation de paiement est un **soft delete** (`status='annule'`, motif, date) : le reçu reste consultable, la numérotation n'est jamais réutilisée.

## 4. Interface (PySide6)

- `MainWindow` : navigation latérale (boutons checkables) + `QStackedWidget` (2 pages) ; services instanciés une fois et injectés.
- `StudentsPage` : recherche live + filtres classe/statut combinés, tableau avec badges `StatusBadge`, actions contextuelles ; les IDs circulent via `Qt.UserRole` (jamais via le texte).
- `StudentDetailsDialog` : historique trié chronologiquement pour le **solde cumulé**, affiché du plus récent au plus ancien ; annulations avec motif.
- `PaymentDialog` : aperçu temps réel du solde après saisie, avertissement de dépassement, refus bloquant.
- `DashboardPage` : `PaymentService.get_overview()` calcule toutes les stats en une passe (une requête SUM par élève).
- Thème : `app/ui/theme.py` (palette + QSS « bleu professionnel éducatif »), composants partagés dans `app/ui/widgets.py`.

## 5. Configuration & chemins

| Élément | Développement | PyInstaller |
|---|---|---|
| Ressources (schéma, seed) | racine du projet | `sys._MEIPASS` |
| DB travail | `%APPDATA%/EduPaie/edupaie.db` | idem |
| Surcharge tests | variable `EDUPAIE_DB` | idem |
| Reçus PDF | `~/Documents/EduPaie/Recus/` | idem |
| Logs | `edupaie.log` (dossier données) | idem |

Au premier lancement : si la DB de travail est absente/vide et qu'une seed embarquée existe, elle est copiée ; le schéma est ensuite toujours initialisé/migré.

## 6. Tests

`tests/test_services.py` (pytest, DB isolée par variable `EDUPAIE_DB`, `Database.reset_instance()`) :
- élèves : création + matricule auto, doublon refusé, validation des noms, suppression protégée ;
- statuts : Non payé → Partiel → Soldé (correctif du bug « Non payé affiché Partiel ») ;
- paiements : dépassement refusé, montant/date/mode invalides, numéros séquentiels uniques, annulation avec restauration du solde, `get_overview` cohérent ;
- reçus : PDF valide depuis le snapshot, **immutabilité du snapshot** après paiements ultérieurs.

```bash
python -m pytest tests/ -v
```

## 7. Décisions de conception

| Décision | Justification |
|---|---|
| Centimes entiers | Élimine les erreurs de virgule flottante sur les soldes |
| Compteur en base + transaction | Numéros uniques même en cas d'accès concurrents |
| Snapshot JSON figé | Ré-impression fidèle d'un reçu, exigence comptable |
| Soft delete des paiements | Auditabilité : aucun reçu disparaît |
| Suppression élève interdite si paiements | Conservation de la chaîne reçus ↔ paiements |
| Schéma auto-migré au démarrage | Déploiements simples (bases anciennes mises à niveau) |
| Services testables hors UI | pytest sans Qt ; `EDUPAIE_DB` pour l'isolation |

## 8. Limites connues & pistes

- Pas d'interface de gestion des plans de frais / classes / années (SQL direct aujourd'hui).
- Export CSV, recherche de reçu par numéro, multilingue : extensibles via les services existants.
- L'impression directe passe par la visionneuse PDF système (pas de QPrinter natif).
