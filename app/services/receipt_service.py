"""
Service de génération des reçus PDF (reportlab)

Le reçu est généré à partir du SNAPSHOT figé stocké en base au moment
de l'enregistrement du paiement : ré-imprimer un reçu produit toujours
exactement le même document, même si l'élève ou ses tarifs ont changé.
"""

import os
import subprocess
import sys
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import RECEIPTS_FOLDER
from app.services.exceptions import NotFoundError

PRIMARY = colors.HexColor("#2c5282")
PRIMARY_LIGHT = colors.HexColor("#4299e1")
SUCCESS = colors.HexColor("#2f855a")
DANGER = colors.HexColor("#c53030")
GREY = colors.HexColor("#4a5568")
LIGHT = colors.HexColor("#edf2f7")


class ReceiptService:
    """Génère et exporte les reçus de paiement en PDF."""

    def __init__(self, payment_service=None):
        self.payment_service = payment_service

    # ------------------------------------------------------------------
    # Génération
    # ------------------------------------------------------------------

    def generate_receipt_pdf(self, payment, output_path: Optional[str] = None) -> str:
        """
        Génère le PDF du reçu d'un paiement.

        Args:
            payment: Objet Payment (le snapshot est chargé depuis la base)
            output_path: Chemin de sortie ; par défaut Documents/EduPaie/Recus/

        Returns:
            Le chemin du fichier PDF généré

        Raises:
            NotFoundError: Si le paiement n'a pas de snapshot
        """
        if self.payment_service is None:
            from app.services.payment_service import PaymentService
            self.payment_service = PaymentService()

        snapshot = self.payment_service.get_payment_snapshot(payment.id)
        if not snapshot:
            raise NotFoundError(
                f"Snapshot introuvable pour le paiement {payment.receipt_no}")

        if output_path is None:
            RECEIPTS_FOLDER.mkdir(parents=True, exist_ok=True)
            output_path = str(
                RECEIPTS_FOLDER / f"recu_{payment.receipt_no}.pdf")

        self._render_pdf(snapshot, output_path)
        return output_path

    def generate_receipt_from_snapshot(self, snapshot: dict, output_path: str) -> str:
        """Génère un PDF depuis un snapshot arbitraire (aperçu / tests)."""
        self._render_pdf(snapshot, output_path)
        return output_path

    # ------------------------------------------------------------------
    # Rendu PDF
    # ------------------------------------------------------------------

    def _render_pdf(self, snapshot: dict, output_path: str):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=1.8 * cm,
            bottomMargin=1.8 * cm,
            title=f"Reçu {snapshot.get('receipt_no', '')}",
            author=snapshot.get("school", {}).get("name", "EduPaie"),
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "RecuTitle", parent=styles["Heading1"], fontSize=20,
            textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=4)
        subtitle_style = ParagraphStyle(
            "RecuSubtitle", parent=styles["Normal"], fontSize=10,
            textColor=GREY, alignment=TA_CENTER)
        section_style = ParagraphStyle(
            "RecuSection", parent=styles["Heading2"], fontSize=12,
            textColor=PRIMARY, spaceBefore=12, spaceAfter=6)
        footer_style = ParagraphStyle(
            "RecuFooter", parent=styles["Normal"], fontSize=8.5,
            textColor=GREY, alignment=TA_CENTER)

        school = snapshot.get("school", {})
        student = snapshot.get("student", {})
        payment = snapshot.get("payment", {})
        balance = snapshot.get("balance", {})

        elements = []

        # En-tête : école + titre
        elements.append(Paragraph(school.get("name", "Établissement"), title_style))
        elements.append(Paragraph(
            f"{school.get('address', '')} — Tél. {school.get('phone', '')}"
            f"{' — ' + school.get('email', '') if school.get('email') else ''}",
            subtitle_style))
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(HRFlowable(width="100%", thickness=1.2, color=PRIMARY))
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("REÇU DE PAIEMENT", title_style))
        elements.append(Paragraph(
            f"N° <b>{snapshot.get('receipt_no', '')}</b>"
            f" — émis le {snapshot.get('receipt_date', '')}",
            subtitle_style))
        elements.append(Spacer(1, 0.6 * cm))

        # Tableau élève
        elements.append(Paragraph("Élève", section_style))
        eleve_rows = [
            ["Nom & prénom", f"{student.get('last_name', '')} {student.get('first_name', '')}"],
            ["Matricule", student.get("matricule", "")],
            ["Classe", student.get("class", "")],
            ["Année scolaire", student.get("school_year", "")],
        ]
        elements.append(self._info_table(eleve_rows))
        elements.append(Spacer(1, 0.4 * cm))

        # Tableau paiement
        elements.append(Paragraph("Paiement", section_style))
        amount = payment.get("amount_formatted", "")
        paiement_rows = [
            ["Date du paiement", self._format_date(payment.get("paid_on", ""))],
            ["Montant payé", amount],
            ["Mode de paiement", payment.get("method", "")],
        ]
        if payment.get("reference"):
            paiement_rows.append(["Référence", payment["reference"]])
        table = self._info_table(paiement_rows)
        table.setStyle(TableStyle([
            ("BACKGROUND", (1, 2), (1, 2), LIGHT),
            ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
            ("FONTSIZE", (1, 2), (1, 2), 13),
            ("TEXTCOLOR", (1, 2), (1, 2), SUCCESS),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.4 * cm))

        # Tableau solde
        elements.append(Paragraph("Situation après paiement", section_style))
        balance_after = balance.get("after_formatted", "")
        solde_rows = [
            ["Solde avant paiement", balance.get("before_formatted", "")],
            ["Montant payé", f"- {amount}"],
            ["Solde restant dû", balance_after],
        ]
        table = self._info_table(solde_rows)
        after_int = balance.get("after_int", 0)
        table.setStyle(TableStyle([
            ("BACKGROUND", (1, 2), (1, 2), LIGHT),
            ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
            ("FONTSIZE", (1, 2), (1, 2), 13),
            ("TEXTCOLOR", (1, 2), (1, 2),
             SUCCESS if after_int == 0 else DANGER),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 1 * cm))

        # Signature
        signature_table = Table(
            [["", "Signature et cachet"], ["", ""], ["", ""]],
            colWidths=[10 * cm, 6 * cm],
            rowHeights=[0.5 * cm, 1.8 * cm, 0.3 * cm])
        signature_table.setStyle(TableStyle([
            ("BOX", (1, 0), (1, -1), 0.75, GREY),
            ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (1, 0), (1, 0), 9),
            ("TEXTCOLOR", (1, 0), (1, 0), GREY),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
        ]))
        elements.append(signature_table)
        elements.append(Spacer(1, 0.8 * cm))
        elements.append(HRFlowable(width="100%", thickness=0.75, color=LIGHT))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph(
            "Ce reçu est généré par EduPaie et sert de preuve de paiement. "
            "Conservez-le : il peut être réimprimé à l'identique grâce à son numéro unique.",
            footer_style))

        doc.build(elements)

    @staticmethod
    def _info_table(rows) -> Table:
        """Construit un tableau label/valeur stylé."""
        table = Table(rows, colWidths=[5.5 * cm, 10.5 * cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10.5),
            ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1a202c")),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Convertit 'AAAA-MM-JJ' en 'JJ/MM/AAAA' (retourne l'entrée si déjà formatée)."""
        try:
            parts = str(date_str).split("-")
            if len(parts) == 3:
                return f"{parts[2]}/{parts[1]}/{parts[0]}"
        except Exception:
            pass
        return str(date_str)

    # ------------------------------------------------------------------
    # Impression directe
    # ------------------------------------------------------------------

    def print_receipt(self, payment) -> str:
        """
        Génère le reçu dans un fichier temporaire et l'ouvre avec la
        visionneuse PDF par défaut du système (permet l'impression directe).
        """
        path = self.generate_receipt_pdf(payment, output_path=None)
        self._open_file(path)
        return path

    @staticmethod
    def _open_file(path: str):
        try:
            if os.name == "nt":
                os.startfile(path)  # Windows
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception:
            # Silencieux : l'utilisateur peut toujours ouvrir le PDF manuellement
            pass
