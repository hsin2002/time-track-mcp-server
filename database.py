
"""
TimeTrack's persistence layer -- MySQL.

Shared by:
    1. FastAPI REST API
    2. FastMCP server

Both use these same database functions.
"""

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

 
# ============================================================
# DATABASE CONFIGURATION
# ============================================================

import os
import threading
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "myhq76.h.filess.io"),
    "database": os.getenv("MYSQL_DATABASE", "timetrack_ironplanet"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "timetrack_ironplanet"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "connection_timeout": 10,
}

_db_initialized = False
_db_init_lock = threading.Lock()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Open a MySQL database connection.
    """

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if not connection.is_connected():
            raise RuntimeError("Could not connect to MySQL database.")

        return connection

    except Error as e:
        raise RuntimeError(
            f"Could not connect to MySQL database: {e}"
        ) from e


# ============================================================
# INITIALIZE DATABASE
# ============================================================



def init_db():
    """
    Create the time_entries table if it does not exist.

    This function is called lazily when the application
    actually needs database access.
    """

    global _db_initialized

    if _db_initialized:
        return

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_name VARCHAR(255) NOT NULL,
                project VARCHAR(255) NOT NULL,
                entry_date DATE NOT NULL,
                hours DECIMAL(10,2) NOT NULL,
                description TEXT NOT NULL
            )
        """)

        conn.commit()

        cursor.execute(
            "SELECT COUNT(*) FROM time_entries"
        )

        count = cursor.fetchone()[0]

        if count == 0:

            seed = [
                (
                    "Asha Patel",
                    "Website Redesign",
                    "2026-09-08",
                    6.5,
                    "Homepage layout",
                ),
                (
                    "Asha Patel",
                    "Website Redesign",
                    "2026-09-09",
                    7.0,
                    "Mobile responsive fixes",
                ),
                (
                    "Asha Patel",
                    "Client Onboarding",
                    "2026-09-10",
                    3.0,
                    "Kickoff call + notes",
                ),
                (
                    "Rahul Mehta",
                    "Website Redesign",
                    "2026-09-08",
                    5.5,
                    "API integration",
                ),
                (
                    "Rahul Mehta",
                    "Internal Tools",
                    "2026-09-09",
                    8.0,
                    "Dashboard bug fixes",
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO time_entries
                (
                    employee_name,
                    project,
                    entry_date,
                    hours,
                    description
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                seed,
            )

            conn.commit()

        _db_initialized = True

    finally:
        cursor.close()
        conn.close()




def ensure_db_initialized():
    global _db_initialized

    if _db_initialized:
        return

    with _db_init_lock:

        if _db_initialized:
            return

        init_db()

        _db_initialized = True




def init_db_old():
    """
    Create the time_entries table if it does not exist.

    Also inserts sample data when the table is empty.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_name VARCHAR(255) NOT NULL,
                project VARCHAR(255) NOT NULL,
                entry_date DATE NOT NULL,
                hours DECIMAL(10,2) NOT NULL,
                description TEXT NOT NULL
            )
        """)

        conn.commit()

        cursor.execute(
            "SELECT COUNT(*) FROM time_entries"
        )

        count = cursor.fetchone()[0]

        if count == 0:

            seed = [
                (
                    "Asha Patel",
                    "Website Redesign",
                    "2026-09-08",
                    6.5,
                    "Homepage layout",
                ),
                (
                    "Asha Patel",
                    "Website Redesign",
                    "2026-09-09",
                    7.0,
                    "Mobile responsive fixes",
                ),
                (
                    "Asha Patel",
                    "Client Onboarding",
                    "2026-09-10",
                    3.0,
                    "Kickoff call + notes",
                ),
                (
                    "Rahul Mehta",
                    "Website Redesign",
                    "2026-09-08",
                    5.5,
                    "API integration",
                ),
                (
                    "Rahul Mehta",
                    "Internal Tools",
                    "2026-09-09",
                    8.0,
                    "Dashboard bug fixes",
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO time_entries
                (
                    employee_name,
                    project,
                    entry_date,
                    hours,
                    description
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                seed,
            )

            conn.commit()

    finally:
        cursor.close()
        conn.close()


# ============================================================
# INTERNAL HELPER
# ============================================================

def _row_to_dict(row) -> dict:
    """
    Convert a MySQL row into a normal Python dictionary.

    MySQL connector returns tuples by default, so the column
    positions are mapped manually.
    """
     
    return {
        "id": row[0],
        "employee_name": row[1],
        "project": row[2],
        "entry_date": (
            row[3].isoformat()
            if hasattr(row[3], "isoformat")
            else str(row[3])
        ),
        "hours": float(row[4]),
        "description": row[5],
    }


# ============================================================
# LIST ALL ENTRIES
# ============================================================

def list_all_entries() -> list[dict]:
    ensure_db_initialized()
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                employee_name,
                project,
                entry_date,
                hours,
                description
            FROM time_entries
            ORDER BY entry_date DESC, id DESC
        """)

        rows = cursor.fetchall()

        return [_row_to_dict(row) for row in rows]

    finally:
        cursor.close()
        conn.close()


# ============================================================
# LOG TIME
# ============================================================

def log_time(
    employee_name: str,
    project: str,
    entry_date: str,
    hours: float,
    description: str = "",
) -> dict:
    ensure_db_initialized()
    if hours <= 0:
        raise ValueError("hours must be a positive number")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO time_entries
            (
                employee_name,
                project,
                entry_date,
                hours,
                description
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                employee_name,
                project,
                entry_date,
                hours,
                description,
            ),
        )

        conn.commit()

        new_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT
                id,
                employee_name,
                project,
                entry_date,
                hours,
                description
            FROM time_entries
            WHERE id = %s
            """,
            (new_id,),
        )

        row = cursor.fetchone()

        return _row_to_dict(row)

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET TIMESHEET
# ============================================================

def get_timesheet(
    employee_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:

    ensure_db_initialized()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        query = """
            SELECT
                id,
                employee_name,
                project,
                entry_date,
                hours,
                description
            FROM time_entries
            WHERE employee_name = %s
        """

        params = [employee_name]

        if start_date:
            query += " AND entry_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND entry_date <= %s"
            params.append(end_date)

        query += " ORDER BY entry_date"

        cursor.execute(query, params)

        rows = cursor.fetchall()

        return [_row_to_dict(row) for row in rows]

    finally:
        cursor.close()
        conn.close()


# ============================================================
# LIST PROJECTS
# ============================================================

def list_projects() -> list[str]:
    ensure_db_initialized()
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT project
            FROM time_entries
            ORDER BY project
        """)

        rows = cursor.fetchall()

        return [row[0] for row in rows]

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET PROJECT SUMMARY
# ============================================================

def get_project_summary(project: str) -> dict:
    ensure_db_initialized()
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                employee_name,
                SUM(hours) AS total_hours
            FROM time_entries
            WHERE project = %s
            GROUP BY employee_name
            ORDER BY employee_name
            """,
            (project,),
        )

        rows = cursor.fetchall()

        if not rows:
            raise ValueError(
                f"No time logged against project '{project}'"
            )

        by_employee = {
            row[0]: float(row[1])
            for row in rows
        }

        return {
            "project": project,
            "total_hours": sum(by_employee.values()),
            "by_employee": by_employee,
        }

    finally:
        cursor.close()
        conn.close()

