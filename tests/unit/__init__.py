# -*- coding: utf-8 -*-
"""
AppTestCase is a subclass of unittest.TestCase for writing unit tests
that will have access to a clean h database.
"""

from unittest import TestCase

from paste.deploy.loadwsgi import appconfig
from pyramid import testing
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from h.models import Base
from h import api

settings = appconfig('config:test.ini', relative_to='.')

class AppTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = engine_from_config(settings)
        cls.Session = sessionmaker(autoflush=False, autocommit=True)
        config = testing.setUp(settings=settings)

    def setUp(self):
        self.connection = self.engine.connect()
        self.db = self.Session(bind=self.connection)
        Base.metadata.bind = self.connection
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        # empty out the database
        for table in reversed(Base.metadata.sorted_tables):
            self.connection.execute(table.delete())
        self.db.close()

        # TODO: clean out ES index for each test
        #from annotator import annotation, document, es
        #document.Document.drop_all()
        #document.Document.create_all()



