# Manuel Utilisateur - EduPaie

## Introduction

EduPaie est une application de gestion des paiements scolaires qui permet de suivre les paiements des élèves, de calculer automatiquement les soldes et de générer des reçus numérotés.

## Démarrage

### Lancement de l'application

1. Double-cliquez sur `main.py` ou exécutez la commande :
```bash
python main.py
```

2. La fenêtre principale s'ouvre avec deux onglets :
   - **Tableau de bord** : vue d'ensemble et statistiques
   - **Élèves** : gestion des élèves et des paiements

## Enregistrer un élève

1. Cliquez sur l'onglet **"Élèves"**
2. Cliquez sur le bouton **"Ajouter un élève"**
3. Remplissez les champs obligatoires (marqués d'un *) :
   - **Nom** : nom de famille de l'élève
   - **Prénom** : prénom de l'élève
   - **Classe** : classe de l'élève (ex: 6ème A, CM2)
   - **Année scolaire** : année en cours (ex: 2024-2025)
   - **Montant des frais de scolarité** : montant total dû pour l'année
4. Cliquez sur **"Enregistrer"**

## Modifier un élève

1. Dans l'onglet **"Élèves"**, sélectionnez l'élève dans la liste
2. Cliquez sur le bouton **"Modifier"**
3. Modifiez les champs nécessaires
4. Cliquez sur **"Enregistrer"**

## Supprimer un élève

1. Dans l'onglet **"Élèves"**, sélectionnez l'élève dans la liste
2. Cliquez sur le bouton **"Supprimer"**
3. Confirmez la suppression
4. **Note** : un élève ayant des paiements ne peut pas être supprimé

## Rechercher un élève

1. Dans l'onglet **"Élèves"**, utilisez la barre de recherche
2. Tapez le nom, prénom ou classe recherché
3. La liste se met à jour automatiquement

## Filtrer par classe

1. Dans l'onglet **"Élèves"**, utilisez le menu déroulant **"Filtrer par classe"**
2. Sélectionnez la classe souhaitée
3. Seuls les élèves de cette classe sont affichés

## Enregistrer un paiement

1. Dans l'onglet **"Élèves"**, sélectionnez l'élève concerné
2. Cliquez sur le bouton **"Enregistrer un paiement"**
3. Remplissez les champs :
   - **Montant du paiement** : montant versé par la famille
   - **Date du paiement** : date du versement
   - **Mode de paiement** : Espèces, Chèque, Virement ou Mobile Money
4. Le système affiche le **solde restant avant paiement**
5. Si le montant dépasse le solde, un message d'erreur s'affiche
6. Cliquez sur **"Enregistrer le paiement"**
7. Un numéro de reçu unique est généré automatiquement

## Consulter l'historique des paiements

1. Dans l'onglet **"Élèves"**, sélectionnez l'élève
2. Cliquez sur le bouton **"Voir détails"**
3. Une fenêtre s'ouvre avec :
   - Les informations de l'élève
   - Le solde actuel et le statut de paiement
   - La liste chronologique de tous les paiements

## Voir les détails d'un reçu

1. Dans la fenêtre de détails de l'élève
2. Sélectionnez un paiement dans l'historique
3. Cliquez sur **"Voir le reçu"**
4. Les détails du reçu s'affichent (numéro, montant, date, mode, solde)

## Imprimer un reçu en PDF

1. Dans la fenêtre de détails de l'élève
2. Sélectionnez un paiement dans l'historique
3. Cliquez sur **"Imprimer le reçu (PDF)"**
4. Choisissez l'emplacement de sauvegarde
5. Le fichier PDF est généré et peut être imprimé

## Tableau de bord

L'onglet **"Tableau de bord"** affiche :

### Statistiques globales
- **Nombre d'élèves** : total des élèves enregistrés
- **Total encaissé** : somme de tous les paiements reçus
- **Total restant dû** : somme des soldes restants
- **Élèves non soldés** : nombre d'élèves qui n'ont pas payé en totalité

### Liste des élèves
- Tableau complet avec statut de paiement
- Filtre par statut : Tous, Soldés, Partiellement payés, Non payés
- Codes couleur :
  - 🟢 Vert : Soldé
  - 🟡 Orange : Partiellement payé
  - 🔴 Rouge : Non payé

## Statuts de paiement

- **Soldé** : l'élève a payé la totalité des frais de scolarité
- **Partiellement payé** : l'élève a effectué des paiements mais il reste un solde
- **Non payé** : aucun paiement n'a été enregistré

## Conseils

- Utilisez la recherche pour trouver rapidement un élève
- Vérifiez régulièrement le tableau de bord pour suivre les encaissements
- Imprimez systématiquement un reçu après chaque paiement
- Conservez une copie des reçus PDF en cas de litige

## Support

En cas de problème ou de question, contactez l'administrateur système.
