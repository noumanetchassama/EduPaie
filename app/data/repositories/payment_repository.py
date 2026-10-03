"""
Repository pour la gestion des paiements (Payment)

Ce fichier contient uniquement les accès aux données SQLite.
Aucune logique d'interface graphique ne doit se trouver ici.
"""

import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from app.models.payment import Payment
from app.data.db import Database
from app.services.exceptions import DatabaseError


class PaymentRepository:
    """Repository pour les opérations CRUD sur les paiements."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()

    def add(self, payment: Payment, snapshot: dict = None) -> int:
        """
        Ajoute un paiement dans la base de données avec son snapshot.

        Utilise une transaction explicite pour garantir l'atomicité :
        - Insertion du paiement
        - Incrémentation du compteur de reçus
        - Sauvegarde du snapshot

        Args:
            payment: Objet Payment à ajouter
            snapshot: Dictionnaire JSON du snapshot du reçu

        Returns:
            int: Identifiant du paiement créé

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        with self.db.transaction() as cursor:
            try:
                # Insérer le paiement
                cursor.execute(
                    """
                    INSERT INTO payment (
                        student_id, school_year_id, amount_int, paid_on,
                        method, reference, receipt_no, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payment.student_id,
                        payment.school_year_id,
                        payment.amount_int,
                        payment.paid_on,
                        payment.method,
                        payment.reference,
                        payment.receipt_no,
                        payment.status
                    )
                )

                payment_id = cursor.lastrowid

                # Sauvegarder le snapshot si fourni
                if snapshot:
                    cursor.execute(
                        """
                        INSERT INTO receipt_snapshot (payment_id, snapshot_json)
                        VALUES (?, ?)
                        """,
                        (payment_id, json.dumps(snapshot, ensure_ascii=False))
                    )

                return payment_id

            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """
        Récupère un paiement à partir de son identifiant.

        Args:
            payment_id: Identifiant du paiement

        Returns:
            Payment | None: Le paiement trouvé ou None s'il n'existe pas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, student_id, school_year_id, amount_int, paid_on,
                   method, reference, receipt_no, status,
                   cancel_reason, cancel_date, created_at
            FROM payment
            WHERE id = ?
            """,
            (payment_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_payment(row)

    def get_by_receipt_no(self, receipt_no: str) -> Optional[Payment]:
        """
        Récupère un paiement à partir de son numéro de reçu.

        Args:
            receipt_no: Numéro de reçu

        Returns:
            Payment | None: Le paiement trouvé ou None s'il n'existe pas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, student_id, school_year_id, amount_int, paid_on,
                   method, reference, receipt_no, status,
                   cancel_reason, cancel_date, created_at
            FROM payment
            WHERE receipt_no = ?
            """,
            (receipt_no,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_payment(row)

    def get_by_student(self, student_id: int, school_year_id: int = None,
                       valid_only: bool = True) -> List[Payment]:
        """
        Récupère les paiements d'un élève.

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire (optionnel)
            valid_only: Si True, ne retourne que les paiements valides (non annulés)

        Returns:
            List[Payment]: Liste des paiements
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if school_year_id and valid_only:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                WHERE student_id = ? AND school_year_id = ? AND status = 'valide'
                ORDER BY paid_on DESC
                """,
                (student_id, school_year_id)
            )
        elif school_year_id:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                WHERE student_id = ? AND school_year_id = ?
                ORDER BY paid_on DESC
                """,
                (student_id, school_year_id)
            )
        elif valid_only:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                WHERE student_id = ? AND status = 'valide'
                ORDER BY paid_on DESC
                """,
                (student_id,)
            )
        else:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                WHERE student_id = ?
                ORDER BY paid_on DESC
                """,
                (student_id,)
            )

        rows = cursor.fetchall()
        return [self._row_to_payment(row) for row in rows]

    def get_total_by_student(self, student_id: int, school_year_id: int = None,
                            valid_only: bool = True) -> int:
        """
        Calcule le total des paiements pour un élève (en cents).

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire (optionnel)
            valid_only: Si True, ne compte que les paiements valides

        Returns:
            int: Total en cents
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if school_year_id and valid_only:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount_int), 0) as total
                FROM payment
                WHERE student_id = ? AND school_year_id = ? AND status = 'valide'
                """,
                (student_id, school_year_id)
            )
        elif school_year_id:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount_int), 0) as total
                FROM payment
                WHERE student_id = ? AND school_year_id = ?
                """,
                (student_id, school_year_id)
            )
        elif valid_only:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount_int), 0) as total
                FROM payment
                WHERE student_id = ? AND status = 'valide'
                """,
                (student_id,)
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount_int), 0) as total
                FROM payment
                WHERE student_id = ?
                """,
                (student_id,)
            )

        row = cursor.fetchone()
        return row['total'] if row else 0

    def update(self, payment: Payment, snapshot: dict = None) -> bool:
        """
        Met à jour un paiement (montant, date, mode, référence).

        Args:
            payment: Objet Payment avec les nouvelles valeurs
            snapshot: Nouveau snapshot du reçu (optionnel)

        Returns:
            bool: True si une ligne a été modifiée

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        if payment.id is None:
            raise ValueError("Impossible de modifier un paiement sans identifiant.")

        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE payment
                    SET amount_int = ?, paid_on = ?, method = ?, reference = ?
                    WHERE id = ?
                    """,
                    (
                        payment.amount_int,
                        payment.paid_on,
                        payment.method,
                        payment.reference,
                        payment.id,
                    ),
                )
                updated = cursor.rowcount > 0

                if updated and snapshot is not None:
                    cursor.execute(
                        """
                        UPDATE receipt_snapshot
                        SET snapshot_json = ?
                        WHERE payment_id = ?
                        """,
                        (json.dumps(snapshot, ensure_ascii=False), payment.id),
                    )
                return updated
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def delete(self, payment_id: int) -> bool:
        """
        Supprime physiquement un paiement (et son snapshot via CASCADE).

        À n'utiliser que pour corriger une saisie erronée : préférer
        l'annulation (soft delete) pour conserver la traçabilité.

        Args:
            payment_id: Identifiant du paiement

        Returns:
            bool: True si le paiement a été supprimé

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute("DELETE FROM payment WHERE id = ?", (payment_id,))
                return cursor.rowcount > 0
            except sqlite3.Error as e:
                raise DatabaseError(f"Erreur lors de la suppression : {e}")

    def cancel(self, payment_id: int, reason: str) -> bool:
        """
        Annule un paiement (soft delete).

        Ne supprime pas physiquement le paiement, mais le marque comme annulé.
        L'historique et la numérotation restent intacts.

        Args:
            payment_id: Identifiant du paiement
            reason: Motif de l'annulation

        Returns:
            bool: True si le paiement a été annulé, sinon False

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE payment
                    SET status = 'annule',
                        cancel_reason = ?,
                        cancel_date = ?
                    WHERE id = ? AND status = 'valide'
                    """,
                    (reason, datetime.now().strftime('%Y-%m-%d'), payment_id)
                )
                return cursor.rowcount > 0
            except sqlite3.Error as e:
                raise DatabaseError(f"Erreur lors de l'annulation : {e}")

    def get_snapshot(self, payment_id: int) -> Optional[dict]:
        """
        Récupère le snapshot d'un reçu.

        Args:
            payment_id: Identifiant du paiement

        Returns:
            dict | None: Snapshot JSON ou None si introuvable
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT snapshot_json
            FROM receipt_snapshot
            WHERE payment_id = ?
            """,
            (payment_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return json.loads(row['snapshot_json'])

    def increment_receipt_counter(self, year: int) -> int:
        """
        Incrémente le compteur de reçus pour une année (opération atomique).

        Cette méthode doit être appelée dans une transaction avec l'insertion
        du paiement pour garantir l'atomicité.

        Args:
            year: Année (ex: 2024)

        Returns:
            int: Nouveau numéro de reçu
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Incrémentation atomique
        cursor.execute(
            """
            UPDATE receipt_counter
            SET last_number = last_number + 1
            WHERE year = ?
            """,
            (year,)
        )

        # Récupérer le nouveau numéro
        cursor.execute(
            """
            SELECT last_number FROM receipt_counter WHERE year = ?
            """,
            (year,)
        )

        row = cursor.fetchone()
        return row['last_number'] if row else 1

    def get_all(self, school_year_id: int = None, valid_only: bool = True) -> List[Payment]:
        """
        Récupère tous les paiements.

        Args:
            school_year_id: Identifiant de l'année scolaire (optionnel)
            valid_only: Si True, ne retourne que les paiements valides

        Returns:
            List[Payment]: Liste des paiements
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if school_year_id and valid_only:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                WHERE school_year_id = ? AND status = 'valide'
                ORDER BY paid_on DESC
                """,
                (school_year_id,)
            )
        elif school_year_id:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                WHERE school_year_id = ?
                ORDER BY paid_on DESC
                """,
                (school_year_id,)
            )
        elif valid_only:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                WHERE status = 'valide'
                ORDER BY paid_on DESC
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, student_id, school_year_id, amount_int, paid_on,
                       method, reference, receipt_no, status,
                       cancel_reason, cancel_date, created_at
                FROM payment
                ORDER BY paid_on DESC
                """
            )

        rows = cursor.fetchall()
        return [self._row_to_payment(row) for row in rows]

    @staticmethod
    def _row_to_payment(row) -> Payment:
        """
        Transforme une ligne SQLite en objet Payment.
        """
        return Payment(
            id=row["id"],
            student_id=row["student_id"],
            school_year_id=row["school_year_id"],
            amount_int=row["amount_int"],
            paid_on=row["paid_on"],
            method=row["method"],
            reference=row["reference"],
            receipt_no=row["receipt_no"],
            status=row["status"],
            cancel_reason=row["cancel_reason"],
            cancel_date=row["cancel_date"],
            created_at=row["created_at"]
        )
