import unittest
from unittest.mock import patch

from Backend.ModelProviders import LocalFirstModelRouter, ModelProviderError


class ModelRouterTests(unittest.TestCase):
    def test_local_success_avoids_cloud(self):
        router = LocalFirstModelRouter(local_model="test", cloud_url="https://cloud.invalid/v1", cloud_model="cloud", cloud_api_key="secret")
        with patch.object(router, "_ollama", return_value='{"type":"final","response":"ok"}') as local, patch.object(router, "_cloud") as cloud:
            reply = router.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(reply.provider, "local")
        local.assert_called_once()
        cloud.assert_not_called()

    def test_cloud_fallback_only_when_fully_configured(self):
        router = LocalFirstModelRouter(cloud_url="https://cloud.invalid/v1", cloud_model="cloud", cloud_api_key="secret")
        with patch.object(router, "_ollama", side_effect=ModelProviderError("offline")), patch.object(router, "_cloud", return_value="fallback") as cloud:
            reply = router.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(reply.provider, "cloud")
        self.assertEqual(reply.text, "fallback")
        cloud.assert_called_once()

    def test_no_cloud_configured_returns_actionable_error(self):
        router = LocalFirstModelRouter(cloud_url="", cloud_model="", cloud_api_key="")
        with patch.object(router, "_ollama", side_effect=ModelProviderError("offline")):
            with self.assertRaisesRegex(ModelProviderError, "cloud fallback is not fully configured"):
                router.complete([{"role": "user", "content": "hi"}])

    def test_provider_timeout_has_lower_bound(self):
        router = LocalFirstModelRouter(timeout_seconds=0)
        self.assertEqual(router.timeout_seconds, 1.0)


if __name__ == "__main__":
    unittest.main()
