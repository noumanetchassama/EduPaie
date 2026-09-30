"""
Tests pour la gestion des paiements
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.paiement import Paiement
from models.eleve import Eleve
from repositories.paiement_repository import PaiementRepository
from repositories.eleve_repository import EleveRepository
from utils.database import Database


class TestPaiements(unittest.TestCase):
    """Tests pour la gestion des paiements"""
    
    @classmethod
    def setUpClass(cls):
        """Initialisation avant tous les tests"""
        cls.db = Database('test_edupaie.db')
        cls.db.initialize_schema()
        cls.eleve_repo = EleveRepository(cls.db)
        cls.paiement_repo = PaiementRepository(cls.db)
        
        # Créer un élève de test
        cls.eleve = Eleve(
            nom="Test",
            prenom="Élève",
            classe="6ème A",
            annee_scolaire="2024-2025",
            montant_du=500.0
        )
        cls.eleve_id = cls.eleve_repo.add(cls.eleve)
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après tous les tests"""
        cls.db.close()
        if os.path.exists('test_edupaie.db'):
            os.remove('test_edupaie.db')
    
    def test_add_paiement(self):
        """Test l'ajout d'un paiement"""
        paiement = Paiement(
            eleve_id=self.eleve_id,
            montant=250.0,
            date_paiement="2024-09-30",
            mode_paiement="especes",
            numero_recu="REC-20240930-00001"
        )
        paiement_id = self.paiement_repo.add(paiement)
        self.assertIsNotNone(paiement_id)
        self.assertGreater(paiement_id, 0)
    
    def test_get_paiement(self):
        """Test la récupération d'un paiement"""
        paiement = Paiement(
            eleve_id=self.eleve_id,
            montant=100.0,
            date_paiement="2024-09-30",
            mode_paiement="cheque",
            numero_recu="REC-20240930-00002"
        )
        paiement_id = self.paiement_repo.add(paiement)
        
        retrieved = self.paiement_repo.get_by_id(paiement_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.montant, 100.0)
        self.assertEqual(retrieved.mode_paiement, "cheque")
    
    def test_get_paiements_by_eleve(self):
        """Test la récupération des paiements d'un élève"""
        paiement1 = Paiement(
            eleve_id=self.eleve_id,
            montant=150.0,
            date_paiement="2024-09-29",
            mode_paiement="virement",
            numero_recu="REC-20240929-00001"
        )
        paiement2 = Paiement(
            eleve_id=self.eleve_id,
            montant=200.0,
            date_paiement="2024-09-30",
            mode_paiement="especes",
            numero_recu="REC-20240930-00003"
        )
        self.paiement_repo.add(paiement1)
        self.paiement_repo.add(paiement2)
        
        paiements = self.paiement_repo.get_by_eleve(self.eleve_id)
        self.assertGreaterEqual(len(paiements), 2)
    
    def test_get_total_by_eleve(self):
        """Test le calcul du total des paiements"""
        paiement = Paiement(
            eleve_id=self.eleve_id,
            montant=300.0,
            date_paiement="2024-09-30",
            mode_paiement="mobile_money",
            numero_recu="REC-20240930-00004"
        )
        self.paiement_repo.add(paiement)
        
        total = self.paiement_repo.get_total_by_eleve(self.eleve_id)
        self.assertGreater(total, 0)


if __name__ == '__main__':
    unittest.main()
