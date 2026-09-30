"""
Constantes de l'application
"""

# Modes de paiement
MODES_PAIEMENT = ['especes', 'cheque', 'virement', 'mobile_money']
MODES_PAIEMENT_LABELS = {
    'especes': 'Espèces',
    'cheque': 'Chèque',
    'virement': 'Virement',
    'mobile_money': 'Mobile Money'
}

# Statuts de paiement
STATUT_SOLDE = "Soldé"
STATUT_PARTIEL = "Partiellement payé"
STATUT_NON_PAYE = "Non payé"

# Configuration base de données
DB_NAME = "edupaie.db"
DB_PATH = "database/edupaie.db"

# Configuration reçus
RECUS_FOLDER = "receipts"
