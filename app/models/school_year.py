"""
Modèle SchoolYear (Année scolaire)
"""

from typing import Optional


class SchoolYear:
    """Représente une année scolaire"""

    def __init__(
        self,
        id: Optional[int] = None,
        label: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_current: bool = False
    ):
        self.id = id
        self.label = label  # Ex: "2024-2025"
        self.start_date = start_date
        self.end_date = end_date
        self.is_current = is_current

    def __repr__(self):
        return f"SchoolYear(id={self.id}, label='{self.label}', is_current={self.is_current})"

    def to_dict(self):
        """Convertit l'année scolaire en dictionnaire"""
        return {
            'id': self.id,
            'label': self.label,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'is_current': self.is_current
        }

    @classmethod
    def from_dict(cls, data):
        """Crée une année scolaire depuis un dictionnaire"""
        return cls(
            id=data.get('id'),
            label=data.get('label'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            is_current=data.get('is_current', False)
        )
