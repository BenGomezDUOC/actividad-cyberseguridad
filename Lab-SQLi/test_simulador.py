import unittest
from unittest.mock import patch
from simulador import app, evaluate


class LabTests(unittest.TestCase):
    def test_normal_and_wrong(self):
        for mode in ("vulnerable", "seguro"):
            with self.subTest(mode=mode):
                self.assertEqual(len(evaluate(mode, "ana", "semilla123")["rows"]), 1)
                self.assertEqual(evaluate(mode, "ana", "incorrecta")["rows"], [])

    def test_tautology_and_comment(self):
        for username, count in (("' OR '1'='1' -- ", 3), ("ana' -- ", 1)):
            with self.subTest(username=username):
                vulnerable = evaluate("vulnerable", username, "incorrecta")
                self.assertEqual(len(vulnerable["rows"]), count)
                self.assertTrue(vulnerable["bypass"])
                safe = evaluate("seguro", username, "incorrecta")
                self.assertEqual(safe["rows"], [])
                self.assertFalse(safe["bypass"])
                self.assertEqual(safe["params"], (username, "incorrecta"))

    def test_errors_and_containment(self):
        self.assertIsNotNone(evaluate("vulnerable", "'", "x")["error"])
        self.assertIsNotNone(evaluate("vulnerable", "ana'; DELETE FROM usuarios; -- ", "x")["error"])
        self.assertEqual(len(evaluate("seguro", "ana", "semilla123")["rows"]), 1)
        with self.assertRaises(ValueError):
            evaluate("seguro", "x" * 161, "x")

    def test_web_controls_and_cases(self):
        client = app.test_client()
        base = "http://127.0.0.1:5000"
        self.assertEqual(client.get("/", base_url=base).status_code, 200)
        self.assertEqual(client.get("/", base_url="http://evil.example").status_code, 403)
        self.assertEqual(client.get("/", base_url=base, environ_overrides={"REMOTE_ADDR": "192.0.2.1"}).status_code, 403)
        self.assertEqual(client.post("/", base_url=base).status_code, 403)
        self.assertIn("No se pudo procesar", client.post("/", base_url=base).text)
        with client.session_transaction(base_url=base) as session:
            token = session["csrf"]
        data = dict(csrf=token, modo="ambos", caso="tautologia")
        response = client.post("/", base_url=base, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Consulta parametrizada segura", response.text)
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
        self.assertEqual(client.post("/", base_url=base, data=data, headers={"Origin": base}).status_code, 200)
        self.assertEqual(client.post("/", base_url=base, data=data, headers={"Origin": "https://evil.example"}).status_code, 403)
        self.assertIn("origen del formulario", client.post("/", base_url=base, data=data, headers={"Origin": "null"}).text)
        stale = dict(data, csrf="formulario-anterior")
        self.assertIn("desactualizado", client.post("/", base_url=base, data=stale).text)
        self.assertEqual(app.config["SESSION_COOKIE_NAME"], "vivero_sqli_session")
        for case in ("normal", "incorrecto", "comentario"):
            data["caso"] = case
            self.assertEqual(client.post("/", base_url=base, data=data).status_code, 200)
        data.update(caso="", usuario="<script>alert(1)</script>", clave="x")
        response = client.post("/", base_url=base, data=data)
        self.assertNotIn("<script>alert(1)</script>", response.text)
        self.assertIn("&lt;script&gt;", response.text)

    def test_startup_binds_loopback(self):
        import runpy
        with patch("flask.Flask.run") as run:
            runpy.run_path("simulador.py", run_name="__main__")
            run.assert_called_once_with(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
