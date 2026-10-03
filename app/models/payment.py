"""
Modèle Payment (Paiement)
Argent stocké en entiers (cents)
"""

from datetime import datetime
from typing import Optional


class Payment:
    """Classe représentant un paiement"""

    def __init__(
        self,
        id: Optional[int] = None,
        student_id: Optional[int] = None,
        school_year_id: Optional[int] = None,
        amount_int: int = 0,
        paid_on: Optional[str] = None,
        method: Optional[str] = None,
        reference: Optional[str] = None,
        receipt_no: Optional[str] = None,
        status: str = 'valide',
        cancel_reason: Optional[str] = None,
        cancel_date: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.student_id = student_id
        self.school_year_id = school_year_id
        self.amount_int = amount_int  # Montant en cents (entier)
        self.paid_on = paid_on
        self.method = method
        self.reference = reference
        self.receipt_no = receipt_no
        self.status = status  # 'valide' ou 'annule'
        self.cancel_reason = cancel_reason
        self.cancel_date = cancel_date
        self.created_at = created_at

    def __repr__(self):
        return f"Payment(id={self.id}, student_id={self.student_id}, amount_int={self.amount_int}, receipt_no='{self.receipt_no}')"

    def to_dict(self):
        """Convertit le paiement en dictionnaire"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'school_year_id': self.school_year_id,
            'amount_int': self.amount_int,
            'paid_on': self.paid_on,
            'method': self.method,
            'reference': self.reference,
            'receipt_no': self.receipt_no,
            'status': self.status,
            'cancel_reason': self.cancel_reason,
            'cancel_date': self.cancel_date,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Crée un paiement depuis un dictionnaire"""
        return cls(
            id=data.get('id'),
            student_id=data.get('student_id'),
            school_year_id=data.get('school_year_id'),
            amount_int=data.get('amount_int', 0),
            paid_on=data.get('paid_on'),
            method=data.get('method'),
            reference=data.get('reference'),
            receipt_no=data.get('receipt_no'),
            status=data.get('status', 'valide'),
            cancel_reason=data.get('cancel_reason'),
            cancel_date=data.get('cancel_date'),
            created_at=data.get('created_at')
        )

    @property
    def is_valid(self) -> bool:
        """Retourne True si le paiement est valide (non annulé)"""
        return self.status == 'valide'

    @property
    def is_cancelled(self) -> bool:
        """Retourne True si le paiement est annulé"""
        return self.status == 'annule'
