"""
Exceptions métier de l'application EduPaie

Ces exceptions sont levées par la couche services et attrapées
par la couche UI pour afficher des messages explicites à l'utilisateur.
"""


class EduPaieException(Exception):
    """Exception de base pour toutes les erreurs métier EduPaie"""
    pass


class ValidationError(EduPaieException):
    """
    Exception levée lors d'une erreur de validation des données.

    Exemples : champ vide, montant négatif, date invalide, format incorrect
    """
    pass


class BusinessRuleError(EduPaieException):
    """
    Exception levée lors d'une violation d'une règle métier.

    Exemples : paiement supérieur au solde, élève inexistant,
                numéro de reçu déjà utilisé, tentative de suppression
                d'un élève avec des paiements
    """
    pass


class NotFoundError(EduPaieException):
    """
    Exception levée lorsqu'une ressource n'est pas trouvée.

    Exemples : élève inexistant, paiement inexistant
    """
    pass


class DatabaseError(EduPaieException):
    """
    Exception levée lors d'une erreur de base de données.

    Exemples : erreur de connexion, violation de contrainte unique
    """
    pass
