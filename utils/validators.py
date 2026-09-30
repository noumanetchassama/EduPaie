"""
Fonctions de validation des données
"""


def validate_nom(value: str) -> bool:
    """Valide un nom (non vide, lettres et espaces uniquement)"""
    if not value or not value.strip():
        return False
    return all(c.isalpha() or c.isspace() or c in "-'" for c in value)


def validate_montant(value: float) -> bool:
    """Valide un montant (positif)"""
    return value > 0


def validate_classe(value: str) -> bool:
    """Valide un nom de classe"""
    if not value or not value.strip():
        return False
    return len(value.strip()) >= 2


def validate_annee_scolaire(value: str) -> bool:
    """Valide une année scolaire (format: YYYY-YYYY)"""
    if not value or not value.strip():
        return False
    parts = value.strip().split('-')
    if len(parts) != 2:
        return False
    try:
        annee1 = int(parts[0])
        annee2 = int(parts[1])
        return annee2 == annee1 + 1 and annee1 >= 2000 and annee1 <= 2100
    except ValueError:
        return False


def validate_mode_paiement(value: str) -> bool:
    """Valide un mode de paiement"""
    modes_valides = ['especes', 'cheque', 'virement', 'mobile_money']
    return value.lower() in modes_valides
