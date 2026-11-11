import sqlite3
import unittest
from core import compare, connect, due, save_test

class CoreTests(unittest.TestCase):
    def test_comparison(self):
        self.assertEqual(compare('Hello, world!', 'hello world'), 100)
        self.assertEqual(compare('one two', 'one'), 50)
        self.assertEqual(compare('hello', ''), 0)
        self.assertEqual(compare('hello', 'one two three'), 0)
        with self.assertRaises(ValueError): compare('', 'hello')

    def test_schedule_and_storage(self):
        db = connect(':memory:')
        self.assertTrue(due(db))
        save_test(db, 70, {'writing': "I'm learning"})
        self.assertFalse(due(db))
        db.execute("UPDATE attempts SET created='2000-01-01T00:00:00'")
        self.assertTrue(due(db))
        db.close()

if __name__ == '__main__': unittest.main()
