"""
Quick setup script for Leave Management System
Run this from the project root directory
"""

import sys
import subprocess
from pathlib import Path

def run_setup():
    print("="*70)
    print("Leave Management System - Quick Setup")
    print("="*70)
    print()
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("⚠ Virtual environment not found.")
        create_venv = input("Create virtual environment? (y/n): ").lower()
        if create_venv == 'y':
            print("Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", "venv"])
            print("✓ Virtual environment created")
            print("\nPlease activate it and run this script again:")
            print("  Windows: venv\\Scripts\\activate")
            print("  Linux/Mac: source venv/bin/activate")
            return
    
    # Check if requirements are installed
    print("Checking dependencies...")
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        print("✓ Dependencies installed")
    except ImportError:
        print("⚠ Some dependencies missing")
        install = input("Install requirements? (y/n): ").lower()
        if install == 'y':
            print("Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ Dependencies installed")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("\n⚠ .env file not found")
        create_env = input("Create .env file with defaults? (y/n): ").lower()
        if create_env == 'y':
            env_content = """DATABASE_URL=sqlite:///./leave_management.db
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=
"""
            env_file.write_text(env_content)
            print("✓ .env file created")
    
    # Initialize database
    print("\nInitializing database...")
    try:
        from app.database import init_db
        init_db()
        print("✓ Database schema created")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return
    
    # Load sample data
    print("\nLoading sample data...")
    load_data = input("Load sample users and data? (y/n): ").lower()
    if load_data == 'y':
        try:
            # Import and run the initialization
            sys.path.insert(0, str(Path.cwd()))
            from scripts.init_sample_data import init_sample_data
            init_sample_data()
        except Exception as e:
            print(f"❌ Error loading sample data: {e}")
            return
    
    print("\n" + "="*70)
    print("✓ Setup Complete!")
    print("="*70)
    print("\nTo start the server:")
    print("  uvicorn app.main:app --reload")
    print("\nAPI Documentation:")
    print("  http://localhost:8000/docs")
    print("="*70)

if __name__ == "__main__":
    run_setup()