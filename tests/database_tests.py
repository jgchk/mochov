import random
import string
from unittest import TestCase

from mochov.database import Database


class EmptyDatabaseTests(TestCase):
    def setUp(self):
        self.db = Database("sqlite:///:memory:")

    def test_get_users_blank(self):
        users = self.db.session.query(Database.User).all()
        self.assertEqual(users, [])

    def test_get_words_blank(self):
        messages = self.db.session.query(Database.Message).all()
        self.assertEqual(messages, [])


class FullDatabaseTests(TestCase):
    def setUp(self):
        self.users = []

        self.db = Database("sqlite:///:memory:")
        self.prep_db()

    def prep_db(self):
        for i in range(10):
            user = self.rand_user()

            for j in range(100):
                message = self.rand_message(user.id)
                user.messages.append(message)

            self.db.session.add(user)
            self.users.append(user)
        self.db.session.commit()

    @staticmethod
    def rand_string(length=8):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def rand_id():
        return str(random.getrandbits(64))

    def rand_message(self, user_id):
        id = self.rand_id()
        content = self.rand_string(length=random.randint(10, 100))
        return Database.Message(id=id, content=content, user_id=user_id)

    def rand_user(self):
        id = self.rand_id()
        username = self.rand_string()
        discriminator = random.randint(0, 9999)
        return Database.User(id=id, username=username, discriminator=discriminator, messages=[])

    def test_get_all_users(self):
        users = self.db.session.query(Database.User).all()
        self.assertEqual(users, self.users)

    def test_get_user(self):
        user = random.choice(self.users)
        user_db = self.db.session.query(Database.User).filter(Database.User.id == user.id).first()
        self.assertEqual(user, user_db)

    def test_get_word_empty_string(self):
        messages = self.db.session.query(Database.Message). \
            filter(Database.Message == ""). \
            all()
        self.assertEqual(messages, [])

    def test_get_user_message(self):
        user = random.choice(self.users)
        rand_message = random.choice(user.messages)
        db_message = self.db.session.query(Database.Message).filter(Database.Message.user_id == user.id).filter(
            Database.Message.content == rand_message.content).all()
        self.assertEqual(db_message, [rand_message])

    def test_add_user_message(self):
        user = random.choice(self.users)

        message = self.rand_message(user.id)
        self.db.session.add(message)
        self.db.session.commit()

        user.messages.append(message)

        user_db = self.db.session.query(Database.User).filter(Database.User.id == user.id).first()
        self.assertEqual(user_db.messages, user.messages)
