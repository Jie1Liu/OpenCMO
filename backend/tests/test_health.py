import unittest

from fastapi.testclient import TestClient

from app.main import app


class HealthApiTest(unittest.TestCase):
    def test_health_endpoint(self) -> None:
        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "aimo-backend"},
        )

    def test_openapi_schema_is_available(self) -> None:
        with TestClient(app) as client:
            response = client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["info"]["title"], "AIMO Backend")


if __name__ == "__main__":
    unittest.main()
