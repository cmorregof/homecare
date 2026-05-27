import unittest

from db.supabase_client import _looks_placeholder


class SupabaseClientTest(unittest.TestCase):
    def test_placeholder_detection_rejects_template_values(self):
        self.assertTrue(_looks_placeholder("https://xxxxx.supabase.co"))
        self.assertTrue(_looks_placeholder("sk-..."))
        self.assertTrue(_looks_placeholder(""))

    def test_placeholder_detection_allows_real_jwt_like_keys(self):
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.real-payload.signature"
        self.assertFalse(_looks_placeholder(key))


if __name__ == "__main__":
    unittest.main()
