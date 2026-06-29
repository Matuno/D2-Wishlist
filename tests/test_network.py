from io import BytesIO
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from d2_wishlist.generator import fetch_json


class FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


class NetworkFetchTests(unittest.TestCase):
    def test_fetch_json_retries_transient_server_errors(self):
        attempts = []

        def fake_urlopen(request, timeout):
            attempts.append(request.full_url)
            if len(attempts) == 1:
                raise HTTPError(request.full_url, 500, "Internal Server Error", hdrs=None, fp=None)
            return FakeResponse(b'{"ok": true}')

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = fetch_json("https://example.test/manifest")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(len(attempts), 2)


if __name__ == "__main__":
    unittest.main()
