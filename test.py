import unittest
import bouncer

class TestBouncer(unittest.TestCase):
    def test_determine_importance(self):
        response = bouncer.determine_importance("Hello, how are you?")
        self.assertFalse(response["important"])

        response = bouncer.determine_importance("I need to talk to you about something important.")
        self.assertTrue(response["important"])

        response = bouncer.determine_importance("heyyyy sup BABADOOK")
        self.assertTrue(response["important"])

if __name__ == '__main__':
    unittest.main()