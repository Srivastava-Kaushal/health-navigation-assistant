from app.db.session import engine, Base
from app.models.document import Document, ExtractedResult

def init_db():
    Base.metadata.create_all(bind=engine)