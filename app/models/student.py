"""
Modèle Student (Élève)
Argent stocké en entiers (cents)
"""

from datetime import datetime
from typing import Optional


class Student:
    """Représente un élève"""

    def __init__(
        self,
        id: Optional[int] = None,
        matricule: Optional[str] = None,
        last_name: Optional[str] = None,
        first_name: Optional[str] = None,
        birth_date: Optional[str] = None,
        class_id: Optional[int] = None,
        parent_name: Optional[str] = None,
        parent_phone: Optional[str] = None,
        parent_email: Optional[str] = None,
        is_active: bool = True,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.matricule = matricule
        self.last_name = last_name
        self.first_name = first_name
        self.birth_date = birth_date
        self.class_id = class_id
        self.parent_name = parent_name
        self.parent_phone = parent_phone
        self.parent_email = parent_email
        self.is_active = is_active
        self.created_at = created_at

    def __repr__(self):
        return f"Student(id={self.id}, matricule='{self.matricule}', last_name='{self.last_name}', first_name='{self.first_name}')"

    def to_dict(self):
        """Convertit l'élève en dictionnaire"""
        return {
            'id': self.id,
            'matricule': self.matricule,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'birth_date': self.birth_date,
            'class_id': self.class_id,
            'parent_name': self.parent_name,
            'parent_phone': self.parent_phone,
            'parent_email': self.parent_email,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Crée un élève depuis un dictionnaire"""
        return cls(
            id=data.get('id'),
            matricule=data.get('matricule'),
            last_name=data.get('last_name'),
            first_name=data.get('first_name'),
            birth_date=data.get('birth_date'),
            class_id=data.get('class_id'),
            parent_name=data.get('parent_name'),
            parent_phone=data.get('parent_phone'),
            parent_email=data.get('parent_email'),
            is_active=data.get('is_active', True),
            created_at=data.get('created_at')
        )
