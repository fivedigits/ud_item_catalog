from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func

engine = create_engine('sqlite:///itemcatalog.db')

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False, unique = True)

    def serialize(self):
        return { 'id' : self.id,
                 'name': self.name}

class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable = False)
    description = Column(String)
    create_date = Column(DateTime, server_default=func.now())

    def serialize(self):
        return { 'id': self.id,
                 'name': self.name,
                 'category_id': self.category_id,
                 'description': self.description }

SQLSession = sessionmaker(bind=engine)

Base.metadata.create_all(engine)
                 
