"""配置模块测试。"""

from unittest.mock import patch

from django.db import models
from django.test import RequestFactory, TestCase

from config.fields import EncryptedCharField
from config.middleware import APILogMiddleware


class EncryptedCharFieldTests(TestCase):
    """EncryptedCharField 测试。"""

    def setUp(self) -> None:
        self.field = EncryptedCharField(max_length=512)

    def test_get_prep_value_encrypts_plain_text(self) -> None:
        encrypted = self.field.get_prep_value("my-secret-value")
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, "my-secret-value")
        self.assertTrue(encrypted.endswith("=="))

    def test_get_prep_value_returns_none_for_none(self) -> None:
        result = self.field.get_prep_value(None)
        self.assertIsNone(result)

    def test_get_prep_value_returns_empty_for_empty(self) -> None:
        result = self.field.get_prep_value("")
        self.assertEqual(result, "")

    def test_get_prep_value_does_not_re_encrypt(self) -> None:
        encrypted = self.field.get_prep_value("secret")
        again = self.field.get_prep_value(encrypted)
        self.assertEqual(encrypted, again)

    def test_from_db_value_decrypts(self) -> None:
        encrypted = self.field.get_prep_value("my-secret")
        decrypted = self.field.from_db_value(encrypted, None, None)
        self.assertEqual(decrypted, "my-secret")

    def test_from_db_value_returns_none(self) -> None:
        result = self.field.from_db_value(None, None, None)
        self.assertIsNone(result)

    def test_from_db_value_returns_plain_text(self) -> None:
        result = self.field.from_db_value("plain-text", None, None)
        self.assertEqual(result, "plain-text")

    def test_to_python_decrypts(self) -> None:
        encrypted = self.field.get_prep_value("secret")
        decrypted = self.field.to_python(encrypted)
        self.assertEqual(decrypted, "secret")

    def test_to_python_returns_none(self) -> None:
        result = self.field.to_python(None)
        self.assertIsNone(result)

    def test_to_python_returns_plain_text(self) -> None:
        result = self.field.to_python("plain")
        self.assertEqual(result, "plain")

    def test_encrypt_decrypt_roundtrip(self) -> None:
        original = "hello-world-123!@#"
        encrypted = self.field.get_prep_value(original)
        decrypted = self.field.from_db_value(encrypted, None, None)
        self.assertEqual(decrypted, original)

    def test_default_max_length(self) -> None:
        field = EncryptedCharField()
        self.assertEqual(field.max_length, 512)


class APILogMiddlewareTests(TestCase):
    """APILogMiddleware 测试。"""

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_logs_request_info(self) -> None:
        request = self.factory.get("/api/test/")
        request.user = type("User", (), {"id": 42})()

        def get_response(req):
            return type("Response", (), {"status_code": 200})()

        middleware = APILogMiddleware(get_response)

        with patch("config.middleware.api_logger.info") as mock_log:
            middleware(request)
            mock_log.assert_called_once()
            log_args = mock_log.call_args[0]
            self.assertEqual(log_args[0], "%s %s %s %s %.3fs")
            self.assertEqual(log_args[1], "GET")
            self.assertEqual(log_args[2], "/api/test/")
            self.assertEqual(log_args[3], 42)
            self.assertEqual(log_args[4], 200)

    def test_logs_anonymous_user(self) -> None:
        request = self.factory.get("/api/anon/")
        request.user = type("User", (), {"id": "anon"})()

        def get_response(req):
            return type("Response", (), {"status_code": 401})()

        middleware = APILogMiddleware(get_response)

        with patch("config.middleware.api_logger.info") as mock_log:
            middleware(request)
            log_args = mock_log.call_args[0]
            self.assertEqual(log_args[3], "anon")
            self.assertEqual(log_args[4], 401)

    def test_logs_pre_auth_without_user(self) -> None:
        request = self.factory.get("/api/pre-auth/")
        if hasattr(request, "user"):
            del request.user

        def get_response(req):
            return type("Response", (), {"status_code": 302})()

        middleware = APILogMiddleware(get_response)

        with patch("config.middleware.api_logger.info") as mock_log:
            middleware(request)
            log_args = mock_log.call_args[0]
            self.assertEqual(log_args[3], "pre-auth")
            self.assertEqual(log_args[4], 302)

    def test_logs_post_request(self) -> None:
        request = self.factory.post("/api/data/")
        request.user = type("User", (), {"id": 1})()

        def get_response(req):
            return type("Response", (), {"status_code": 201})()

        middleware = APILogMiddleware(get_response)

        with patch("config.middleware.api_logger.info") as mock_log:
            middleware(request)
            log_args = mock_log.call_args[0]
            self.assertEqual(log_args[1], "POST")
            self.assertEqual(log_args[2], "/api/data/")
            self.assertEqual(log_args[4], 201)
