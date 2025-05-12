import os
import sys
from app import app
from init_db import initialize_database

def setup_application():
    """Set up the application and database"""
    print("🚀 Setting up Agricultural Supply Chain Management System...")
    
    # Create necessary directories
    dirs_to_create = [
        app.instance_path,  # For database
        os.path.join(app.static_folder, 'uploads'),  # For file uploads
        os.path.join(app.static_folder, 'images'),  # For images
    ]
    
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"📁 Created directory: {directory}")
            except Exception as e:
                print(f"❌ Failed to create directory {directory}: {e}")
                sys.exit(1)
    
    # Initialize database
    if initialize_database():
        print("✨ Setup completed successfully!")
        print("\nYou can now run the application with:")
        print("python app.py")
    else:
        print("❌ Setup failed!")
        sys.exit(1)

if __name__ == '__main__':
    setup_application() 