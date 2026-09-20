from database import get_connection


try:
    conn = get_connection()

    print("✅ MySQL connection successful!")

    cursor = conn.cursor()

    cursor.execute("SELECT DATABASE()")
    database = cursor.fetchone()

    print("Database:", database[0])

    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()

    print("MySQL version:", version[0])

    cursor.close()
    conn.close()

    print("✅ Connection closed.")

except Exception as e:
    print("❌ MySQL connection failed:")
    print(e)