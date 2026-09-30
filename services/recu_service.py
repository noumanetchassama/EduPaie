"""
Service pour la génération de reçus PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from models.eleve import Eleve
from models.paiement import Paiement
from services.paiement_service import PaiementService


class RecuService:
    """Service pour générer des reçus PDF"""
    
    def __init__(self):
        self.paiement_service = PaiementService()
    
    def generer_recu_pdf(self, paiement: Paiement, eleve: Eleve, output_path: str):
        """Génère un reçu PDF pour un paiement"""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Style personnalisé pour le titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        # Style pour les en-têtes
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=10
        )
        
        # Style pour le texte normal
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=5
        )
        
        # Titre
        elements.append(Paragraph("REÇU DE PAIEMENT", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Informations de l'école (à personnaliser)
        ecole_info = [
            ["ÉCOLE / ÉTABLISSEMENT", ""],
            ["Adresse:", "123 Rue de l'École"],
            ["Téléphone:", "01 23 45 67 89"],
            ["", ""],
        ]
        
        ecole_table = Table(ecole_info, colWidths=[5*cm, 8*cm])
        ecole_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.darkblue),
        ]))
        elements.append(ecole_table)
        elements.append(Spacer(1, 1*cm))
        
        # Numéro de reçu et date
        recu_info = [
            ["Numéro de reçu:", paiement.numero_recu],
            ["Date d'émission:", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["", ""],
        ]
        
        recu_table = Table(recu_info, colWidths=[5*cm, 8*cm])
        recu_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ]))
        elements.append(recu_table)
        elements.append(Spacer(1, 1*cm))
        
        # Informations de l'élève
        elements.append(Paragraph("Informations de l'élève", header_style))
        
        eleve_info = [
            ["Nom:", eleve.nom],
            ["Prénom:", eleve.prenom],
            ["Classe:", eleve.classe],
            ["Année scolaire:", eleve.annee_scolaire],
        ]
        
        eleve_table = Table(eleve_info, colWidths=[5*cm, 8*cm])
        eleve_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(eleve_table)
        elements.append(Spacer(1, 1*cm))
        
        # Détails du paiement
        elements.append(Paragraph("Détails du paiement", header_style))
        
        mode_label = PaiementService.MODES_PAIEMENT_LABELS.get(paiement.mode_paiement, paiement.mode_paiement)
        solde = self.paiement_service.get_solde(eleve.id)
        
        paiement_info = [
            ["Date du paiement:", paiement.date_paiement],
            ["Montant payé:", f"{paiement.montant:.2f} €"],
            ["Mode de paiement:", mode_label],
            ["Solde restant:", f"{solde:.2f} €"],
        ]
        
        paiement_table = Table(paiement_info, colWidths=[5*cm, 8*cm])
        paiement_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.green),
            ('TEXTCOLOR', (1, 3), (1, 3), colors.red if solde > 0 else colors.green),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(paiement_table)
        elements.append(Spacer(1, 2*cm))
        
        # Signature
        signature_info = [
            ["", "Signature"],
            ["", ""],
            ["", "Cachet de l'établissement"],
        ]
        
        signature_table = Table(signature_info, colWidths=[8*cm, 5*cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), TA_CENTER),
            ('ALIGN', (1, 2), (1, 2), TA_CENTER),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 12),
            ('FONTSIZE', (1, 2), (1, 2), 10),
            ('TEXTCOLOR', (1, 2), (1, 2), colors.grey),
        ]))
        elements.append(signature_table)
        elements.append(Spacer(1, 1*cm))
        
        # Pied de page
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "Ce reçu sert de preuve de paiement. En cas de litige, présentez ce document.",
            footer_style
        ))
        
        # Générer le PDF
        doc.build(elements)
        
        return output_path
    
    def imprimer_recu(self, paiement: Paiement, eleve: Eleve):
        """Imprime directement un reçu (alternative PDF)"""
        # Pour l'instant, on génère un PDF et on laisse l'utilisateur l'imprimer
        # Une implémentation complète utiliserait QPrinter
        import tempfile
        import os
        import subprocess
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        self.generer_recu_pdf(paiement, eleve, temp_path)
        
        # Ouvrir le PDF avec le lecteur par défaut
        try:
            if os.name == 'nt':  # Windows
                os.startfile(temp_path)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.call(['xdg-open', temp_path])
        except:
            pass
        
        return temp_path
