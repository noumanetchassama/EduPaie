"""
Modèle Class (Classe scolaire)
"""

from typing import Optional


class ClassModel:
    """Représente une classe scolaire"""

    def __init__(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        level: Optional[str] = None,
        school_year_id: Optional[int] = None,
        date_creation: Optional[str] = None
    ):
        self.id = id
        self.name = name  # Ex: "6ème A"
        self.level = level  # Ex: "6ème"
        self.school_year_id = school_year_id
        self.date_creation = date_creation

    def __repr__(self):
        return f"ClassModel(id={self.id}, name='{self.name}', level='{self.level}')"

    def to_dict(self):
        """Convertit la classe en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'school_year_id': self.school_year_id,
            'date_creation': self.date_creation
        }

    @classmethod
    def from_dict(cls, data):
        """Crée une classe depuis un dictionnaire"""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            level=data.get('level'),
            school_year_id=data.get('school_year_id'),
            date_creation=data.get('date_creation')
        )
