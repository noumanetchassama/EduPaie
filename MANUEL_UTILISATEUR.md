# Manuel utilisateur — EduPaie

Application de gestion des paiements de scolarité. Ce manuel décrit l'utilisation quotidienne : élèves, paiements, reçus et tableau de bord.

## Démarrage

Lancez `python main.py` (ou `EduPaie.exe`). L'application s'ouvre sur le **Tableau de bord**. La barre latérale permet de naviguer entre :

- **Tableau de bord** — vue d'ensemble
- **Élèves** — gestion des inscriptions et des paiements
- **Classes** — niveaux, séries et frais de scolarité
- **Journal d'audit** — traçabilité des opérations

En bas de la barre latérale, la liste déroulante **« Année scolaire consultée »** permet de consulter les données d'une autre année (voir section 6) ; le bouton **+** à côté crée une nouvelle année scolaire.

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
| **Déplacer vers une autre classe…** | Transfère l'élève (voir ci-dessous) |

> Les reçus sont **réimprimables à l'identique** : le contenu est figé en base au moment de l'émission, même si l'élève change de classe ou si les tarifs évoluent.

Par défaut, les reçus sont aussi enregistrés dans `~/Documents/EduPaie/Recus/`.

### Déplacer un élève vers une autre classe

Dans la fiche élève, cliquez sur **« Déplacer vers une autre classe… »**, choisissez la nouvelle classe puis validez :

- l'élève change de classe immédiatement ;
- son **total dû est recalculé** automatiquement (frais de la nouvelle classe) ;
- ses paiements déjà enregistrés sont **conservés** ;
- le transfert est **tracé dans le journal d'audit** (« Transfert de classe : « 6ème A » → « 5ème A » »).

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

## 5. Journal d'audit (onglet dédié)

L'onglet **Journal d'audit** liste toutes les opérations tracées : **qui** (utilisateur système) a **fait quoi** (création, modification, suppression, annulation) et **sur quoi** (élève, paiement, classe, année scolaire), avec le détail (motif d'annulation, champs modifiés, transfert de classe…).

- **Filtres** : par élément (élèves / paiements / classes / années) et par action.
- Chaque ligne indique la date et l'heure, l'action (en couleur), le libellé de l'élément (nom, n° de reçu…) et le compte utilisateur.
- Le journal est **automatique** : aucune action supplémentaire n'est nécessaire lors de la saisie.

---

## 6. Consulter une année scolaire précédente

En bas de la barre latérale, la liste déroulante **« Année scolaire consultée »** affiche toutes les années connues (l'année courante est marquée « — courante ») :

1. Choisissez une année : le **tableau de bord**, la liste des **élèves** (soldes et statuts de cette année) et les **classes** s'actualisent ; les fiches élèves montrent les **paiements et reçus de cette année-là**.
2. Repassez sur l'année courante pour revenir à la saisie normale.

> Les paiements s'enregistrent **toujours dans l'année courante** : sur une année antérieure, le bouton « Enregistrer un paiement » est désactivé.

### Créer une nouvelle année scolaire

Cliquez sur le bouton **+** sous la liste des années :

1. Saisissez le libellé au format `AAAA-AAAA` (ex. `2025-2026`).
2. Laissez cochée **« Recopier les classes et leurs frais »** pour retrouver la même grille de classes.
3. Cochez **« Définir comme année courante »** uniquement au moment de la rentrée : les nouveaux paiements y seront enregistrés.

> Astuce : créez la nouvelle année **sans** la définir comme courante pour préparer la rentrée tout en continuant la saisie de l'année en cours.

---

## 7. Questions fréquentes

**Où sont stockées mes données ?**
Dans votre dossier utilisateur : `%APPDATA%/EduPaie/edupaie.db` (Windows) ou `~/.config/EduPaie/` (Linux/macOS). Pensez à le sauvegarder.

**Puis-je saisir un paiement supérieur au solde ?**
Non, par conception. Le formulaire vous avertit dès la saisie et l'enregistrement est bloqué.

**Un paiement a été saisi en double, que faire ?**
Fiche élève → sélectionnez le paiement → **Annuler ce paiement…** avec un motif. L'historique conserve la trace ; le solde est restauré.

**Le reçu d'un paiement annulé est-il conservé ?**
Oui. Il apparaît « Annulé » dans l'historique et reste consultable/téléchargeable.

**Comment changer les tarifs d'une classe ?**
Onglet **Classes** → sélectionnez la classe → **Modifier** → changez le montant. Les soldes des élèves de la classe sont recalculés automatiquement.

**Comment voir ce qu'un élève devait l'année dernière ?**
Barre latérale → sélectionnez l'année précédente dans la liste déroulante, puis ouvrez la fiche de l'élève : soldes et paiements affichés concernent cette année.
