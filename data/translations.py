import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Translations(SqlAlchemyBase):
    __tablename__ = 'translations'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    first_language = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    second_language = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')
