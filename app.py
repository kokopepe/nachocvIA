import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY environment variable is not set")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    try:
        # Import models here to ensure they're registered before create_all
        from models import InterviewQuestion, Message
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")

        # Import routes after database initialization
        import routes
        logger.info("Routes imported successfully")
    except Exception as e:
        logger.error(f"Error during application setup: {e}")
        raise