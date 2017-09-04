from unittest import TestCase

from mochov.markov import Markov


class MarkovTests(TestCase):
    def setUp(self):
        self.markov = Markov()

    def test_generate_sentence(self):
        user = User()

