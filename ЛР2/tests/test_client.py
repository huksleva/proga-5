import unittest
from unittest.mock import Mock

import requests

from huksleva_openweather import OpenWeatherClient, OpenWeatherError


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.response = self.session.get.return_value
        self.response.status_code = 200
        self.response.json.return_value = {"cod": 200, "main": {"temp": 12}}
        self.client = OpenWeatherClient("secret", session=self.session)

    def test_current_parameters(self):
        self.assertEqual(self.client.current("Moscow")["main"]["temp"], 12)
        self.session.get.assert_called_once_with(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": "Moscow", "appid": "secret", "units": "metric", "lang": "ru"},
            timeout=10,
        )

    def test_forecast_string_status(self):
        self.response.json.return_value = {"cod": "200", "list": []}
        self.assertEqual(self.client.forecast("Moscow")["list"], [])
        self.assertTrue(self.session.get.call_args.args[0].endswith("/forecast"))

    def test_http_error(self):
        self.response.status_code = 401
        self.response.json.return_value = {"cod": 401}
        with self.assertRaises(OpenWeatherError) as caught:
            self.client.current("Moscow")
        self.assertEqual(caught.exception.status_code, 401)

    def test_transport_error_hides_key(self):
        self.session.get.side_effect = requests.Timeout("url?appid=secret")
        with self.assertRaises(OpenWeatherError) as caught:
            self.client.current("Moscow")
        self.assertNotIn("secret", str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)

    def test_invalid_json(self):
        self.response.json.side_effect = ValueError()
        with self.assertRaises(OpenWeatherError):
            self.client.current("Moscow")

    def test_invalid_payload(self):
        self.response.json.return_value = []
        with self.assertRaises(OpenWeatherError):
            self.client.current("Moscow")

    def test_empty_city_does_not_send_request(self):
        with self.assertRaises(ValueError):
            self.client.current(" ")
        self.session.get.assert_not_called()

    def test_external_session_not_closed(self):
        self.client.close()
        self.session.close.assert_not_called()


if __name__ == "__main__":
    unittest.main()
