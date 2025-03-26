from sqlalchemy import Column, Integer, String, JSON
from .database import Base

class ClothingItem(Base):
    __tablename__ = "clothes"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    image_url = Column(String)
    attributes = Column(JSON)  # {"type": "shirt", "color": "blue"}