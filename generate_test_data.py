"""
Script de génération de données de test pour EduPaie
Crée 15+ élèves avec des paiements variés (soldés, partiels, non payés)
"""

from datetime import datetime, timedelta
from repository.database import Database
from repository.eleve_repository import EleveRepository
from repository.paiement_repository import PaiementRepository
from services.paiement_service import PaiementService


def generate_test_data():
    """Génère des données de test"""
    
    db = Database()
    db.initialize_schema()
    
    eleve_repo = EleveRepository(db)
    paiement_repo = PaiementRepository(db)
    paiement_service = PaiementService(paiement_repo, eleve_repo)
    
    # Données des élèves
    eleves_data = [
        # Élèves soldés
        {"nom": "Martin", "prenom": "Jean", "classe": "6ème A", "annee": "2024-2025", "montant": 500, "statut": "solde"},
        {"nom": "Dubois", "prenom": "Marie", "classe": "6ème A", "annee": "2024-2025", "montant": 500, "statut": "solde"},
        {"nom": "Bernard", "prenom": "Pierre", "classe": "5ème B", "annee": "2024-2025", "montant": 550, "statut": "solde"},
        {"nom": "Petit", "prenom": "Sophie", "classe": "4ème C", "annee": "2024-2025", "montant": 600, "statut": "solde"},
        {"nom": "Robert", "prenom": "Lucas", "classe": "3ème A", "annee": "2024-2025", "montant": 650, "statut": "solde"},
        
        # Élèves partiellement payés
        {"nom": "Richard", "prenom": "Emma", "classe": "6ème B", "annee": "2024-2025", "montant": 500, "statut": "partiel"},
        {"nom": "Durand", "prenom": "Thomas", "classe": "5ème A", "annee": "2024-2025", "montant": 550, "statut": "partiel"},
        {"nom": "Moreau", "prenom": "Léa", "classe": "4ème B", "annee": "2024-2025", "montant": 600, "statut": "partiel"},
        {"nom": "Simon", "prenom": "Hugo", "classe": "3ème B", "annee": "2024-2025", "montant": 650, "statut": "partiel"},
        {"nom": "Michel", "prenom": "Chloé", "classe": "6ème C", "annee": "2024-2025", "montant": 500, "statut": "partiel"},
        
        # Élèves non payés
        {"nom": "Garcia", "prenom": "Antoine", "classe": "5ème C", "annee": "2024-2025", "montant": 550, "statut": "non_paye"},
        {"nom": "David", "prenom": "Camille", "classe": "4ème A", "annee": "2024-2025", "montant": 600, "statut": "non_paye"},
        {"nom": "Bertrand", "prenom": "Maxime", "classe": "3ème C", "annee": "2024-2025", "montant": 650, "statut": "non_paye"},
        {"nom": "Roux", "prenom": "Manon", "classe": "6ème A", "annee": "2024-2025", "montant": 500, "statut": "non_paye"},
        {"nom": "Fournier", "prenom": "Nathan", "classe": "5ème B", "annee": "2024-2025", "montant": 550, "statut": "non_paye"},
        {"nom": "Lemoine", "prenom": "Jade", "classe": "4ème C", "annee": "2024-2025", "montant": 600, "statut": "non_paye"},
    ]
    
    modes_paiement = ['especes', 'cheque', 'virement', 'mobile_money']
    
    print("Génération des données de test...")
    print(f"Nombre d'élèves à créer: {len(eleves_data)}")
    
    eleve_ids = []
    
    # Créer les élèves
    for i, data in enumerate(eleves_data, 1):
        from models.eleve import Eleve
        eleve = Eleve(
            nom=data["nom"],
            prenom=data["prenom"],
            classe=data["classe"],
            annee_scolaire=data["annee"],
            montant_du=data["montant"]
        )
        eleve_id = eleve_repo.add(eleve)
        eleve_ids.append((eleve_id, data))
        print(f"{i}. Élève créé: {data['nom']} {data['prenom']} ({data['classe']}) - {data['montant']}€")
    
    # Créer les paiements selon le statut
    print("\nGénération des paiements...")
    
    paiement_counter = 1
    
    for eleve_id, data in eleve_ids:
        statut = data["statut"]
        montant_du = data["montant"]
        
        if statut == "solde":
            # Payer tout en plusieurs fois
            nb_paiements = 2 if montant_du > 500 else 1
            montant_par_paiement = montant_du / nb_paiements
            
            for j in range(nb_paiements):
                date_paiement = (datetime.now() - timedelta(days=30*j)).strftime("%Y-%m-%d")
                mode = modes_paiement[j % len(modes_paiement)]
                
                from models.paiement import Paiement
                paiement = Paiement(
                    eleve_id=eleve_id,
                    montant=montant_par_paiement,
                    date_paiement=date_paiement,
                    mode_paiement=mode,
                    numero_recu=f"REC-{date_paiement.replace('-', '')}-{paiement_counter:05d}"
                )
                paiement_repo.add(paiement)
                paiement_counter += 1
            
            print(f"  - {data['nom']} {data['prenom']}: Soldé ({nb_paiements} paiements)")
        
        elif statut == "partiel":
            # Payer 50-70%
            pourcentage = 0.5 + (hash(eleve_id) % 3) * 0.1  # 50%, 60% ou 70%
            montant_paye = montant_du * pourcentage
            
            nb_paiements = 2
            montant_par_paiement = montant_paye / nb_paiements
            
            for j in range(nb_paiements):
                date_paiement = (datetime.now() - timedelta(days=15*j)).strftime("%Y-%m-%d")
                mode = modes_paiement[j % len(modes_paiement)]
                
                from models.paiement import Paiement
                paiement = Paiement(
                    eleve_id=eleve_id,
                    montant=montant_par_paiement,
                    date_paiement=date_paiement,
                    mode_paiement=mode,
                    numero_recu=f"REC-{date_paiement.replace('-', '')}-{paiement_counter:05d}"
                )
                paiement_repo.add(paiement)
                paiement_counter += 1
            
            print(f"  - {data['nom']} {data['prenom']}: Partiellement payé ({montant_paye:.2f}€/{montant_du}€)")
        
        elif statut == "non_paye":
            # Aucun paiement
            print(f"  - {data['nom']} {data['prenom']}: Non payé")
    
    print("\n=== Résumé ===")
    print(f"Élèves créés: {len(eleve_ids)}")
    
    # Statistiques
    total_eleves = len(eleve_ids)
    soldes = sum(1 for _, d in eleve_ids if d["statut"] == "solde")
    partiels = sum(1 for _, d in eleve_ids if d["statut"] == "partiel")
    non_payes = sum(1 for _, d in eleve_ids if d["statut"] == "non_paye")
    
    print(f"  - Soldés: {soldes}")
    print(f"  - Partiellement payés: {partiels}")
    print(f"  - Non payés: {non_payes}")
    
    total_du = sum(d["montant"] for _, d in eleve_ids)
    print(f"\nMontant total dû: {total_du:.2f}€")
    
    db.close()
    print("\nDonnées de test générées avec succès!")


if __name__ == "__main__":
    generate_test_data()
