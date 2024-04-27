import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    translations = orm.relationship("Translations", back_populates='user')
