import sqlite3
import os

def fix_database():
    """Add missing is_active column to users table"""
    db_path = "./leave_management.db"  # Adjust path if needed
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        print("Looking for database files...")
        for file in os.listdir('.'):
            if file.endswith('.db'):
                print(f"Found: {file}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if is_active column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        print("Existing columns in users table:", columns)
        
        if 'is_active' not in columns:
            # Add the missing column
            print("Adding 'is_active' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
            conn.commit()
            print("✅ Successfully added 'is_active' column to users table")
        else:
            print("✅ 'is_active' column already exists")
            
        # Verify the fix
        cursor.execute("SELECT id, email, is_active FROM users LIMIT 5")
        users = cursor.fetchall()
        print("Sample users:", users)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()