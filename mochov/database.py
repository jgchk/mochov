from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
Session = sessionmaker()


class Database:
    def __init__(self, conn_string):
        self.engine = create_engine(conn_string)
        self.session = Session(bind=self.engine)
        Base.metadata.create_all(self.engine)

    class User(Base):
        __tablename__ = "users"

        id = Column(String(64), primary_key=True)
        username = Column(String(32), nullable=False)
        discriminator = Column(Integer, nullable=False)
        markov = Column(String(), nullable=False)

        def __repr__(self):
            return "<User(id='{}', username='{}', discriminator='{:d}', markov='{}')>".format(self.id, self.username,
                                                                                              self.discriminator,
                                                                                              self.markov)
