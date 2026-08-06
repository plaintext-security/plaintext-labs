import unittest
from urllib.parse import urlparse, parse_qs
import app


class BuildAuthUrl(unittest.TestCase):
    def test_includes_required_params(self):
        q = parse_qs(urlparse(app.build_auth_url("abc123")).query)
        self.assertEqual(q["response_type"], ["code"])
        self.assertEqual(q["client_id"], ["corp-app"])
        self.assertEqual(q["redirect_uri"], ["http://localhost:3000/callback"])
        self.assertEqual(q["scope"], ["openid"])
        self.assertEqual(q["state"], ["abc123"])

    def test_points_at_auth_endpoint(self):
        self.assertIn("/realms/corp/protocol/openid-connect/auth",
                      app.build_auth_url("x"))


class BuildExchangeCurl(unittest.TestCase):
    def test_contains_grant_code_secret_redirect(self):
        c = app.build_exchange_curl("THECODE")
        self.assertIn("grant_type=authorization_code", c)
        self.assertIn("code=THECODE", c)
        self.assertIn("client_secret=corp-app-secret", c)
        self.assertIn("redirect_uri=http://localhost:3000/callback", c)
        self.assertIn("/protocol/openid-connect/token", c)


class RenderCallback(unittest.TestCase):
    def test_valid_code_shows_code_and_exchange(self):
        html = app.render_callback({"code": ["XYZ"], "state": ["s1"]}, "s1")
        self.assertIn("XYZ", html)
        self.assertIn("grant_type=authorization_code", html)

    def test_state_mismatch_refuses_and_hides_exchange(self):
        html = app.render_callback({"code": ["XYZ"], "state": ["bad"]}, "s1")
        self.assertIn("CSRF", html)
        self.assertNotIn("grant_type=authorization_code", html)

    def test_missing_code_reports_it(self):
        html = app.render_callback({"state": ["s1"]}, "s1")
        self.assertIn("No code", html)

    def test_keycloak_error_is_surfaced(self):
        # A real Keycloak error redirect still carries state, so it passes the
        # state gate and reaches the error branch.
        html = app.render_callback(
            {"error": ["access_denied"], "error_description": ["user said no"],
             "state": ["s1"]}, "s1")
        self.assertIn("access_denied", html)
        self.assertNotIn("grant_type=authorization_code", html)

    def test_none_expected_state_refuses(self):
        html = app.render_callback({"code": ["X"]}, None)
        self.assertIn("CSRF", html)
        self.assertNotIn("grant_type=authorization_code", html)

    def test_reflected_values_are_escaped(self):
        html = app.render_callback(
            {"code": ["<script>x</script>"], "state": ["s1"]}, "s1")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
