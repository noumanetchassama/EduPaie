# Manuel utilisateur — EduPaie

Application de gestion des paiements de scolarité. Ce manuel décrit l'utilisation quotidienne : élèves, paiements, reçus et tableau de bord.

## Démarrage

Lancez `python main.py` (ou `EduPaie.exe`). L'application s'ouvre sur le **Tableau de bord**. La barre latérale permet de naviguer entre :

- **Tableau de bord** — vue d'ensemble
- **Élèves** — gestion des inscriptions et des paiements
- **Classes** — niveaux, séries et frais de scolarité

L'année scolaire en cours est affichée en bas de la barre latérale.

---

## 1. Gérer les élèves (onglet Élèves)

### Ajouter un élève
1. Cliquez sur **＋ Nouvel élève** (en haut à droite).
2. Renseignez : **Nom**, **Prénom**, **Classe**, et si besoin date de naissance et coordonnées du parent.
3. **Matricule** : laissez vide pour qu'il soit généré automatiquement (ex. `2026-6EMEA-0001`).
4. Cliquez sur **Enregistrer**.

> Le montant des frais dus est **défini par classe** (plans de frais) et appliqué automatiquement à chaque élève de la classe.

### Rechercher et filtrer
- **Recherche** : tapez un nom, un prénom ou un matricule — la liste se filtre en direct.
- **Classe** : sélectionnez une classe dans la liste déroulante.
- **Statut** : filtrez les élèves Soldés / Partiellement payés / Non payés.

Les filtres se combinent (ex. « 6ème A » + « Non payés »).

### Modifier / supprimer
- Sélectionnez un élève → **Modifier**.
- **Supprimer** demande une confirmation ; elle est **refusée** si l'élève a des paiements (les reçus émis doivent rester consultables).

---

## 2. Enregistrer un paiement

1. Sélectionnez un élève → **Enregistrer un paiement**.
2. Le dialogue affiche le **solde restant dû** de l'élève.
3. Saisissez le **montant en FCFA** (ex. `25 000`) : un message indique en temps réel le solde après paiement.
   - ⚠ **Si le montant dépasse le solde, l'enregistrement est refusé** : un paiement ne peut jamais rendre le solde négatif.
4. Choisissez la **date** (pas de date future) et le **mode de paiement** : Espèces, Chèque, Virement, Mobile Money. Une **référence** (n° de chèque…) est optionnelle.
5. Validez : un **numéro de reçu unique** (ex. `REC-2024-000023`) est attribué automatiquement.

---

## 3. Historique et reçus (fiche élève)

Double-cliquez sur un élève (ou **Voir la fiche**) :

- En-tête : identité, **statut** (badge coloré), solde / payé / total dû.
- **Historique chronologique** : date, montant, mode, n° de reçu, **solde après paiement**, statut (Valide / Annulé).

Pour chaque paiement sélectionné :

| Action | Effet |
|---|---|
| **Voir le reçu** | Aperçu à l'écran (montant, solde après paiement…) |
| **Télécharger le reçu (PDF)** | Enregistre le PDF à l'emplacement choisi |
| **Imprimer le reçu** | Ouvre le PDF dans la visionneuse → impression |
| **Annuler ce paiement…** | Motif obligatoire ; le reçu reste dans l'historique, le solde est recalculé |

> Les reçus sont **réimprimables à l'identique** : le contenu est figé en base au moment de l'émission, même si l'élève change de classe ou si les tarifs évoluent.

Par défaut, les reçus sont aussi enregistrés dans `~/Documents/EduPaie/Recus/`.

### Corriger ou supprimer un paiement

Dans la fiche élève, sélectionnez un paiement dans l'historique :

| Action | Effet |
|---|---|
| **Modifier ce paiement…** | Corrige le montant, la date, le mode ou la référence. Le **numéro de reçu est conservé** ; le solde ne peut pas devenir négatif. |
| **Annuler ce paiement…** | Motif obligatoire ; le paiement reste visible « Annulé » dans l'historique. À privilégier pour garder une trace. |
| **Supprimer ce paiement** | Suppression définitive (double confirmation) : le reçu n'est plus consultable. Réservé aux saisies erronées. |

---

## 4. Gérer les classes (onglet Classes)

La page **Classes** liste toutes les classes avec leur niveau, leurs **frais annuels en FCFA**, l'échéance et le nombre d'élèves inscrits.

- **＋ Nouvelle classe** : nom (ex. « 6ème C »), niveau, montant des frais.
- **Modifier** : renommer la classe ou **changer les frais** — les soldes de tous les élèves de la classe sont recalculés automatiquement.
- **Supprimer** : refusé si des élèves sont encore inscrits (déplacez-les d'abord).

> Le total dû d'un élève = frais de scolarité de sa classe. Modifier les frais d'une classe met donc à jour le « Total dû » de chaque élève concerné.

---

## 5. Tableau de bord

- **Cartes** : élèves inscrits, total encaissé, total restant dû, élèves non soldés.
- **Répartition** : pourcentages Soldés / Partiels / Non payés.
- **Liste des élèves** : triable et **filtrable par statut** ; **double-clic** = ouvrir la fiche.

---

## 6. Questions fréquentes

**Où sont stockées mes données ?**
Dans votre dossier utilisateur : `%APPDATA%/EduPaie/edupaie.db` (Windows) ou `~/.config/EduPaie/` (Linux/macOS). Pensez à le sauvegarder.

**Puis-je saisir un paiement supérieur au solde ?**
Non, par conception. Le formulaire vous avertit dès la saisie et l'enregistrement est bloqué.

**Un paiement a été saisi en double, que faire ?**
Fiche élève → sélectionnez le paiement → **Annuler ce paiement…** avec un motif. L'historique conserve la trace ; le solde est restauré.

**Le reçu d'un paiement annulé est-il conservé ?**
Oui. Il apparaît « Annulé » dans l'historique et reste consultable/téléchargeable.

**Comment changer les tarifs d'une classe ?**
Les montants sont dans la table `fee_plan` de la base (un outil de gestion des plans de frais peut être ajouté ultérieurement).
