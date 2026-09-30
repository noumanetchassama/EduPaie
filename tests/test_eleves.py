"""
Tests pour la gestion des élèves
"""

import unittest
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.eleve import Eleve
from repositories.eleve_repository import EleveRepository
from utils.database import Database


class TestEleves(unittest.TestCase):
    """Tests pour la gestion des élèves"""
    
    @classmethod
    def setUpClass(cls):
        """Initialisation avant tous les tests"""
        cls.db = Database('test_edupaie.db')
        cls.db.initialize_schema()
        cls.repo = EleveRepository(cls.db)
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après tous les tests"""
        cls.db.close()
        if os.path.exists('test_edupaie.db'):
            os.remove('test_edupaie.db')
    
    def test_add_eleve(self):
        """Test l'ajout d'un élève"""
        eleve = Eleve(
            nom="Test",
            prenom="Élève",
            classe="6ème A",
            annee_scolaire="2024-2025",
            montant_du=500.0
        )
        eleve_id = self.repo.add(eleve)
        self.assertIsNotNone(eleve_id)
        self.assertGreater(eleve_id, 0)
    
    def test_get_eleve(self):
        """Test la récupération d'un élève"""
        eleve = Eleve(
            nom="Test2",
            prenom="Élève",
            classe="5ème B",
            annee_scolaire="2024-2025",
            montant_du=550.0
        )
        eleve_id = self.repo.add(eleve)
        
        retrieved = self.repo.get_by_id(eleve_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.nom, "Test2")
        self.assertEqual(retrieved.classe, "5ème B")
    
    def test_update_eleve(self):
        """Test la modification d'un élève"""
        eleve = Eleve(
            nom="Test3",
            prenom="Élève",
            classe="4ème C",
            annee_scolaire="2024-2025",
            montant_du=600.0
        )
        eleve_id = self.repo.add(eleve)
        
        eleve.montant_du = 650.0
        success = self.repo.update(eleve)
        self.assertTrue(success)
        
        updated = self.repo.get_by_id(eleve_id)
        self.assertEqual(updated.montant_du, 650.0)
    
    def test_delete_eleve(self):
        """Test la suppression d'un élève"""
        eleve = Eleve(
            nom="Test4",
            prenom="Élève",
            classe="3ème A",
            annee_scolaire="2024-2025",
            montant_du=650.0
        )
        eleve_id = self.repo.add(eleve)
        
        success = self.repo.delete(eleve_id)
        self.assertTrue(success)
        
        deleted = self.repo.get_by_id(eleve_id)
        self.assertIsNone(deleted)
    
    def test_search_eleve(self):
        """Test la recherche d'élèves"""
        eleve1 = Eleve(nom="Dupont", prenom="Jean", classe="6ème A", annee_scolaire="2024-2025", montant_du=500.0)
        eleve2 = Eleve(nom="Dupont", prenom="Marie", classe="6ème B", annee_scolaire="2024-2025", montant_du=500.0)
        self.repo.add(eleve1)
        self.repo.add(eleve2)
        
        results = self.repo.search("Dupont")
        self.assertGreaterEqual(len(results), 2)


if __name__ == '__main__':
    unittest.main()
