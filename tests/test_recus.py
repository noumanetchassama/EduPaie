"""
Tests pour la génération de reçus
"""

import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.paiement import Paiement
from models.eleve import Eleve
from repositories.paiement_repository import PaiementRepository
from repositories.eleve_repository import EleveRepository
from services.recu_service import RecuService
from utils.database import Database


class TestRecus(unittest.TestCase):
    """Tests pour la génération de reçus"""
    
    @classmethod
    def setUpClass(cls):
        """Initialisation avant tous les tests"""
        cls.db = Database('test_edupaie.db')
        cls.db.initialize_schema()
        cls.eleve_repo = EleveRepository(cls.db)
        cls.paiement_repo = PaiementRepository(cls.db)
        cls.recu_service = RecuService()
        
        # Créer un élève de test
        cls.eleve = Eleve(
            nom="Test",
            prenom="Élève",
            classe="6ème A",
            annee_scolaire="2024-2025",
            montant_du=500.0
        )
        cls.eleve_id = cls.eleve_repo.add(cls.eleve)
        
        # Créer un paiement de test
        cls.paiement = Paiement(
            eleve_id=cls.eleve_id,
            montant=250.0,
            date_paiement="2024-09-30",
            mode_paiement="especes",
            numero_recu="REC-20240930-00001"
        )
        cls.paiement_id = cls.paiement_repo.add(cls.paiement)
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après tous les tests"""
        cls.db.close()
        if os.path.exists('test_edupaie.db'):
            os.remove('test_edupaie.db')
    
    def test_generer_recu_pdf(self):
        """Test la génération d'un reçu PDF"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp_path = tmp.name
        
        try:
            result = self.recu_service.generer_recu_pdf(
                self.paiement,
                self.eleve,
                tmp_path
            )
            self.assertEqual(result, tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_recu_service_initialization(self):
        """Test l'initialisation du service de reçus"""
        self.assertIsNotNone(self.recu_service)


if __name__ == '__main__':
    unittest.main()
