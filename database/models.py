from base import Thing, tup
from sqlalchemy import (
    Column,
    Integer,
    String,
    Unicode,
    Boolean
)

class Subreddit(Thing):
    _id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    excluded = Column(Boolean, default=False)
    banned = Column(Boolean, default=False)

class Redditor(Thing):
    _id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    excluded = Column(Boolean, default=False)
    banned = Column(Boolean, default=False)