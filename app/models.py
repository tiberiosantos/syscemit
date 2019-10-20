# -*- coding: utf-8 -*-

import csv
import os

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from config import basedir

from .extensions import db


class CRUDMixin():
    __table_args__ = ({'extend_existing': True}, )
    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def create(cls, commit=True, **kwargs):
        instance = cls(**kwargs)
        return instance.save(commit=commit)

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    @classmethod
    def get(cls, id):
        return cls.query.get(id)

    @classmethod
    def get_or_404(cls, id):
        return cls.query.get_or_404(id)

    def update(self, commit=True, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return commit and self.save() or self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()


class UserType(CRUDMixin, db.Model):
    __tablename__ = 'user_types'
    description = db.Column(db.String(25), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    users = db.relationship('User', backref='user_type', lazy='dynamic')

    @classmethod
    def populate(cls):
        user_types = [('Administrador', 'admin'), ('Funcionário', 'employee')]
        user_types = [cls(description=d, role=r) for d, r in user_types]
        db.session.bulk_save_objects(user_types)
        db.session.commit()

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.description)


class User(CRUDMixin, UserMixin, db.Model):
    __tablename__ = 'users'
    name = db.Column(db.String(255), nullable=False)
    login = db.Column(db.String(30), nullable=False)
    _pwd_hash = db.Column(db.String(255), nullable=False)
    user_type_id = db.Column(db.Integer,
                             db.ForeignKey('user_types.id'),
                             nullable=False)

    @classmethod
    def fetch(cls, search, criteria, order, page):
        joins = filters_ = orders = ()

        if criteria and search:
            if criteria == 'type':
                joins += (UserType, )
                filters_ += (
                    cls.user_type_id == UserType.id,
                    UserType.description.ilike('%' + search + '%'),
                )
                orders += (getattr(UserType.description, order)(), )
            else:
                filters_ = (getattr(cls, criteria).ilike('%' + search + '%'), )
                orders += (getattr(getattr(cls, criteria), order)(), )
        elif search:
            filters_ += (cls.name.ilike('%' + search + '%'), )

        if not orders:
            orders += (cls.name.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self._pwd_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._pwd_hash, password)

    def is_admin(self):
        return self.user_type.role == 'admin'

    def has_permissions(self, *roles):
        return self.user_type.role in roles

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.login)


class State(CRUDMixin, db.Model):
    __tablename__ = 'states'
    name = db.Column(db.String(20), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    cities = db.relationship('City', backref='state', lazy='dynamic')

    @classmethod
    def populate(cls):
        path = os.path.join(basedir, 'seeds', 'states.tsv')
        with open(path) as f:
            reader = csv.DictReader(f, delimiter='\t')
            states = [cls(name=row['ESTADO'], uf=row['UF']) for row in reader]
        db.session.bulk_save_objects(states)
        db.session.commit()

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.name)


class City(CRUDMixin, db.Model):
    __tablename__ = 'cities'
    name = db.Column(db.String(40), nullable=False)
    state_id = db.Column(db.Integer,
                         db.ForeignKey('states.id'),
                         nullable=False)
    registries = db.relationship('Registry', backref='city', lazy='dynamic')
    deceased = db.relationship('Deceased', backref='city', lazy='dynamic')
    addresses = db.relationship('Address', backref='city', lazy='dynamic')

    @classmethod
    def populate(cls):
        states = {s.name: int(s.id) for s in State.query.all()}
        path = os.path.join(basedir, 'seeds', 'cities.tsv')
        with open(path) as f:
            reader = csv.DictReader(f, delimiter='\t')
            cities = [
                cls(name=row['CIDADE'], state_id=states[row['ESTADO']])
                for row in reader
            ]
        db.session.bulk_save_objects(cities)
        db.session.commit()

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.name)


class Address(CRUDMixin, db.Model):
    __tablename__ = 'addresses'
    street = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(255), nullable=False)
    cep = db.Column(db.String(8), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    home_address = db.relationship('Deceased',
                                   foreign_keys='Deceased.home_address_id',
                                   backref='address_home',
                                   lazy='dynamic')
    death_address = db.relationship('Deceased',
                                    foreign_keys='Deceased.death_address_id',
                                    backref='address_death',
                                    lazy='dynamic')

    @classmethod
    def fetch(cls, search, criteria, order, page):
        joins = filters_ = orders = ()

        if criteria and search:
            if criteria == 'city':
                joins += (City, )
                filters_ += (
                    cls.city_id == City.id,
                    City.name.ilike('%' + search + '%'),
                )
                orders += (getattr(City.name, order)(), )
            else:
                filters_ = (getattr(cls, criteria).ilike('%' + search + '%'), )
                orders += (getattr(getattr(cls, criteria), order)(), )
        elif search:
            filters_ += (cls.street.ilike('%' + search + '%'), )

        if not orders:
            orders += (cls.street.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.number)


class Doctor(CRUDMixin, db.Model):
    __tablename__ = 'doctors'
    name = db.Column(db.String(255), nullable=False)
    crm = db.Column(db.String(20), nullable=False)
    deceased = db.relationship('Deceased', backref='doctors', lazy='dynamic')

    @classmethod
    def fetch(cls, search, criteria, order, page):
        joins = filters_ = orders = ()

        if criteria and search:
            filters_ += (getattr(cls, criteria).ilike('%' + search + '%'), )
        elif search:
            filters_ += (cls.name.ilike('%' + search + '%'), )

        if criteria and order:
            orders += (getattr(getattr(cls, criteria), order)(), )
        else:
            orders += (cls.name.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.name)


class Registry(CRUDMixin, db.Model):
    __tablename__ = 'registries'
    name = db.Column(db.String(255), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    deceased = db.relationship('Deceased', backref='registry', lazy='dynamic')

    @classmethod
    def fetch(cls, search, criteria, order, page):
        joins = filters_ = orders = ()

        if criteria and search:
            if criteria == 'city':
                joins += (City, )
                filters_ += (
                    cls.city_id == City.id,
                    City.name.ilike('%' + search + '%'),
                )
                orders += (getattr(City.name, order)(), )
            else:
                filters_ = (getattr(cls, criteria).ilike('%' + search + '%'), )
                orders += (getattr(getattr(cls, criteria), order)(), )
        elif search:
            filters_ += (cls.name.ilike('%' + search + '%'), )

        if not orders:
            orders += (cls.name.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.name)


class CivilStates(CRUDMixin, db.Model):
    __tablename__ = 'civil_states'
    description = db.Column(db.String(15), nullable=False)
    deceased = db.relationship('Deceased',
                               backref='civil_states',
                               lazy='dynamic')

    @classmethod
    def populate(cls):
        civil_states = [
            'Solteiro(a)', 'Casado(a)', 'Divorciado(a)', 'Viúvo(a)',
            'Separado(a)'
        ]
        civil_states = [cls(description=e) for e in civil_states]
        db.session.bulk_save_objects(civil_states)
        db.session.commit()

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.name)


class Ethnicity(CRUDMixin, db.Model):
    __tablename__ = 'ethnicities'
    description = db.Column(db.String(10), nullable=False)
    deceased = db.relationship('Deceased', backref='ethnicity', lazy='dynamic')

    @classmethod
    def populate(cls):
        ethnicities = ['Brancos', 'Pardos', 'Negros', 'Indígenas', 'Amarelos']
        ethnicities = [cls(description=e) for e in ethnicities]
        db.session.bulk_save_objects(ethnicities)
        db.session.commit()

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.description)


class Zone(CRUDMixin, db.Model):
    __tablename__ = 'zones'
    description = db.Column(db.String(40), nullable=False)
    complement = db.Column(db.String(10))
    graves = db.relationship('Grave', backref='zone', lazy='dynamic')

    @classmethod
    def fetch(cls, search, criteria, order, page):
        joins = filters_ = orders = ()

        if criteria and search:
            filters_ += (getattr(cls, criteria).ilike('%' + search + '%'), )
        elif search:
            filters_ += (cls.description.ilike('%' + search + '%'), )

        if criteria and order:
            orders += (getattr(getattr(cls, criteria), order)(), )
        else:
            orders += (cls.description.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.description)


class Grave(CRUDMixin, db.Model):
    __tablename__ = 'graves'
    street = db.Column(db.String(5), nullable=False)
    number = db.Column(db.String(5), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    deceased = db.relationship('Deceased', backref='grave', lazy='dynamic')

    @classmethod
    def fetch(cls, search, criteria, order, page):
        joins = filters_ = orders = ()

        if criteria and search:
            if criteria == 'zone':
                joins += (Zone, )
                filters_ += (
                    cls.zone_id == Zone.id,
                    Zone.description.ilike('%' + search + '%'),
                )
                orders += (getattr(Zone.description, order)(), )
            else:
                filters_ = (getattr(cls, criteria).ilike('%' + search + '%'), )
                orders += (getattr(getattr(cls, criteria), order)(), )
        elif search:
            filters_ += (cls.street.ilike('%' + search + '%'), )

        if not orders:
            orders += (cls.street.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    def __repr__(self):
        return '{0}({1} {2})'.format(self.__class__.__name__, self.street,
                                     self.number)


memberships = db.Table(
    'memberships',
    db.Column('filiation_id',
              db.Integer,
              db.ForeignKey('filiations.id'),
              primary_key=True),
    db.Column('deceased_id',
              db.Integer,
              db.ForeignKey('deceased.id'),
              primary_key=True))


class Deceased(CRUDMixin, db.Model):
    name = db.Column(db.String(255))
    age = db.Column(db.Integer)
    birth_date = db.Column(db.Date)
    death_datetime = db.Column(db.DateTime, nullable=False)
    gender = db.Column(db.Boolean, nullable=False)
    cause = db.Column(db.String(1500), nullable=False)
    registration = db.Column(db.String(40), nullable=False)
    home_address_number = db.Column(db.String(5))
    home_address_complement = db.Column(db.String(255))
    birthplace_id = db.Column(db.Integer, db.ForeignKey('cities.id'))
    civil_state_id = db.Column(db.Integer, db.ForeignKey('civil_states.id'))
    home_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    death_address_id = db.Column(db.Integer,
                                 db.ForeignKey('addresses.id'),
                                 nullable=False)
    death_address_number = db.Column(db.String(5))
    death_address_complement = db.Column(db.String(255))
    doctor_id = db.Column(db.Integer,
                          db.ForeignKey('doctors.id'),
                          nullable=False)
    ethnicity_id = db.Column(db.Integer,
                             db.ForeignKey('ethnicities.id'),
                             nullable=False)
    grave_id = db.Column(db.Integer,
                         db.ForeignKey('graves.id'),
                         nullable=False)
    registry_id = db.Column(db.Integer,
                            db.ForeignKey('registries.id'),
                            nullable=False)
    filiations = db.relationship('Filiation',
                                 secondary=memberships,
                                 lazy='subquery',
                                 backref=db.backref('deceased', lazy=True))

    @classmethod
    def fetch(cls, search, criteria, order, page):
        """
        TODO: Refactor queries and include another fields to search.
        """
        joins = filters_ = orders = ()

        if criteria and search:
            filters_ += (getattr(cls, criteria).ilike('%' + search + '%'), )
        elif search:
            filters_ += (cls.name.ilike('%' + search + '%'), )

        if criteria and order:
            orders += (getattr(getattr(cls, criteria), order)(), )
        else:
            orders += (cls.name.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.name)


class Filiation(CRUDMixin, db.Model):
    __tablename__ = 'filiations'
    name = db.Column(db.String(255), nullable=False)

    @classmethod
    def fetch(cls, search, criteria, order, page):
        joins = filters_ = orders = ()

        if criteria and search:
            filters_ += (getattr(cls, criteria).ilike('%' + search + '%'), )
        elif search:
            filters_ += (cls.name.ilike('%' + search + '%'), )

        if criteria and order:
            orders += (getattr(getattr(cls, criteria), order)(), )
        else:
            orders += (cls.name.asc(), )
        return cls.query.join(*joins).filter(*filters_).order_by(
            *orders).paginate(page,
                              per_page=current_app.config['PER_PAGE'],
                              error_out=False)

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.name)
