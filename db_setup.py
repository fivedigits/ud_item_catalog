# -*- coding: utf-8 -*-
"""Module containing class definitions for ORM (sqlalchemy)."""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func

ENGINE = create_engine('sqlite:///itemcatalog.db')

BASE = declarative_base()


class User(BASE):
    """Container class for user data. Has no methods. Needed for
    ORM.

    Attributes:
        id (int): key.
        name (str): name.
        email (str): email, must be UNIQUE (SQL).
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, nullable=False, unique=True)


class Category(BASE):
    """Container class for category data. Has serialize()
    method suitable for JSON serialization.

    Attributes:
        id (int): key.
        name (str): name.
        creator_id (int): Integer key with key from User.
        create_date (DateTime): DateTime, defaults to now().
    """
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    creator_id = Column(String, ForeignKey('users.id'), nullable=False)
    create_date = Column(DateTime, server_default=func.now())

    def serialize(self):
        """Returns the fields of self as a dict for JSON
        serialization.

        Returns:
            dict containing id and name.
        """
        return {'id': self.id,
                'name': self.name}


class Item(BASE):
    """Container class for item data in the SQL database.
    Has serialize() method, which is suitable for json.dumps().

    Attributes:
        id (int): key.
        name (str): name.
        category_id (int): key from Category.
        description (str): item description.
        create_date (DateTime): defaults to now().
        creator_id (int): key from User.
    """
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    description = Column(String)
    create_date = Column(DateTime, server_default=func.now())
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    def serialize(self):
        """Serialize self to a dict for JSON serialization.

        Returns:
            A dict containing items fields except creator_*.
        """
        return {'id': self.id,
                'name': self.name,
                'category_id': self.category_id,
                'description': self.description}


SQLSESSION = sessionmaker(bind=ENGINE)

BASE.metadata.create_all(ENGINE)
