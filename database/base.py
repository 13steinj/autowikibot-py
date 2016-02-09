# If you couldn't tell, reddit and it's database structure have heavily
# influenced this file, and everything in this folder probably.
from __future__ import print_function
from functools import wraps
from sqlalchemy import (
    create_engine,
    or_,
)
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///autowikipedia_database.db', echo=True)

table_registry = {}
class ThingMeta(DeclarativeMeta):
    def __init__(cls, name, bases, attrs):
        super(ThingMeta, cls).__init__(name, bases, attrs)
        if len(cls.mro()) > 2:
            cls.__table__.create(checkfirst=True)
        table_registry[name] = cls

Thing = declarative_base(bind=engine, name="Thing", metaclass=ThingMeta)
session = sessionmaker(bind=engine)()

def noThingAllowed(func):
    @wraps(func)
    def wrapped(*a, **kw):
        if a[0] == Thing or type(a[0]) == Thing:
            raise NotImplementedError("This property/method can not be used on Thing archetypes")
        return func(*a, **kw)
    return wrapped

class class_property(object):
    """A decorator that combines @classmethod and @property.
    http://stackoverflow.com/a/8198300/120999
    """
    def __init__(self, function):
        self.function = function
    def __get__(self, instance, cls):
        return self.function(cls)

@noThingAllowed
def __tablename__(cls):
    if len(cls.mro()) <= 2:
        raise RuntimeError("No raw Thing can have a table nor be committed")
    return cls.__name__.lower()

@noThingAllowed
def c(cls):
    return cls.__table__.c

@classmethod
@noThingAllowed
def _create(cls, **kwargs):
    for i in getattr(cls, '_essentials', []):
        if i not in kwargs:
            raise RuntimeError("%s is required on creation!" % i)
    return cls(**kwargs)

@noThingAllowed
def _commit(self):
    session.commit()

@classmethod
@noThingAllowed
def _new(cls, **kwargs):
    ret = cls._create(**kwargs)
    session.add(ret)
    ret._commit()
    return ret

@classmethod
@noThingAllowed
def _byID(cls, ids, return_dict=True, ignore_missing=False):
    ids, single = tup(ids, True)

    for x in ids:
       if not isinstance(x, (int, long)):
           raise ValueError('non-integer thing_id in %r' % ids)

    if single:
        expression = cls.c._id==ids[0]
    else:
        expression = or_(*[cls.c._id==id for id in ids])

    items = cls._query(expression)
    ret = {item._id: item for item in items}
    missing = []
    for i in ids:
        if i not in ret:
            missing.append(i)
    if missing and not ignore_missing:
        raise NotFound("%s %s" % (cls.__name__, missing))
    for i in missing:
        ids.remove(i)

    if single:
        return ret[ids[0]] if ids else None
    elif return_dict:
        return ret
    else:
        return filter(None, (ret.get(i) for i in ids))

@classmethod
@noThingAllowed
def _by_names(cls, name, return_dict=True, ignore_missing=False):
    names, single = tup(names, True)

    for x in names:
       if not isinstance(x, (str, unicode)):
           raise ValueError('non-unicode name in %r' % names)

    if single:
        expression = cls.c.name==names[0]
    else:
        expression = or_(*[cls.c.name==name for name in names])

    items = cls._query(expression)
    ret = {item.name: item for item in items}
    missing = []
    for i in names:
        if i not in ret:
            missing.append(i)
    if missing and not ignore_missing:
        raise NotFound("%s %s" % (cls.__name__, missing))
    for i in missing:
        names.remove(i)

    if single:
        return ret[names[0]] if names else None
    elif return_dict:
        return ret
    else:
        return filter(None, (ret.get(i) for i in names))

def base36encode(number):
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be positive')
    alphabet, base36 = ['0123456789abcdefghijklmnopqrstuvwxyz', '']
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36 or alphabet[0]

def tup(item, ret_is_single=False):
    """Forces casting of item to a tuple (for a list) or generates a
    single element tuple (for anything else)"""
    #return true for iterables, except for strings, which is what we want
    if hasattr(item, '__iter__'):
        return (item, False) if ret_is_single else item
    else:
        return ((item,), True) if ret_is_single else (item,)

@property
@noThingAllowed
def _id36(self):
    return base36encode(self._id)

@property
@noThingAllowed
def _fullname(self):
    return "%s_%s" % (self.__tablename__, self._id36)

@classmethod
@noThingAllowed
def _byID36(cls, id36s, return_dict=True, **kw):
    id36s, single = tup(id36s, True)

    ids = [int(x, 36) for x in id36s]
    things = cls._byID(ids, return_dict=True, **kw)

    things = {thing._id36: thing for thing in things.itervalues()}
    if single:
        return things.values()[0]
    elif return_dict:
        return things
    else:
        return filter(None, (things.get(i) for i in id36s))

@classmethod
@noThingAllowed
def _by_fullname(cls, fullnames, return_dict=True, **kw):
    fullnames, single = tup(id36s, True)

    ids = [int(x.split('_')[1], 36) for x in fullnames]
    searchclass = table_registry[fullnames[0].split('_')[0]]
    things = searchclass._byID(ids, return_dict=True, **kw)

    things = {thing._fullname: thing for thing in things.itervalues()}
    if single:
        return things.values()[0]
    elif return_dict:
        return things
    else:
        return filter(None, (things.get(i) for i in id36s))

@classmethod
@noThingAllowed
def _query(cls, *rules):
    return session.query(cls).filter(*rules)

Thing.__tablename__ = class_property(__tablename__)
Thing.c = class_property(c)
Thing._new = _new
Thing._create = _create
Thing._commit = _commit
Thing._byID = _byID
Thing._id36 = _id36
Thing._byID36 = _byID36
Thing._fullname = _fullname
Thing._by_fullname = _by_fullname
Thing._query = _query


del __tablename__
del c
del _new
del _create
del _commit
del _byID
del _id36
del _byID36
del _fullname
del _by_fullname
del _query