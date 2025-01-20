from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    # Get Supabase credentials from environment variables
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    dbname = os.getenv('DB_NAME')

    # Construct database URL
    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"
    
    # Configure Flask app
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the app with SQLAlchemy
    db.init_app(app)
    
    # Create all tables within app context
    with app.app_context():
        try:
            # Enable PostgreSQL extensions if needed
            db.session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            db.session.commit()
            
            # Create tables
            db.create_all()
            print("Successfully connected to Supabase!")
        except Exception as e:
            print(f"Database connection error: {e}")


