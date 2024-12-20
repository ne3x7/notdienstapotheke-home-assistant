"""API definition."""

# pylint: disable=R0902,R0917

from __future__ import annotations

from dataclasses import dataclass
from json import JSONDecodeError
from typing import Tuple, Optional

import logging
from datetime import datetime
import re
import gzip
import requests
from seleniumwire import webdriver
from selenium.webdriver import ChromeOptions

from .const import API_ENDPOINT

_LOGGER = logging.getLogger(__name__)


@dataclass
class Apotheke:
    """Class to represent a pharmacy (Apotheke)."""

    name: str
    street: str
    plz: str
    ort: str
    distance: float
    location: Tuple[float, float]
    phone: str
    fax: str | None
    email: str | None
    datetime_from: datetime
    datetime_to: datetime

    @classmethod
    def from_source(cls, result: dict) -> "Apotheke":
        """Parse JSON response from API."""
        return cls(
            name=result["name"],
            street=result["strasse"],
            plz=result["plz"],
            ort=result["ort"],
            distance=result["distanz"],
            location=(result["latitude"], result["longitude"]),
            phone=result["telefon"],
            fax=result["fax"],
            email=result["email"],
            datetime_from=datetime.strptime(
                result["startdatum"] + " " + result["startzeit"], "%d.%m.%Y %H:%M"
            ),
            datetime_to=datetime.strptime(
                result["enddatum"] + " " + result["endzeit"], "%d.%m.%Y %H:%M"
            ),
        )

    def to_dict(self) -> dict:
        """Prepare a dictionary representation for use in Home Assistant."""
        return {
            "name": self.name,
            "street": self.street,
            "plz": self.plz,
            "ort": self.ort,
            "distance": self.distance,
            "location": self.location,
            "phone": self.phone,
            "fax": self.fax,
            "email": self.email,
            "datetime_from": self.datetime_from,
            "datetime_to": self.datetime_to,
        }


class Aponet:
    """Class to handle the API calls."""

    def __init__(
        self,
        plzort: str,
        date: Optional[str] = None,
        street: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[int] = 5,
    ):
        self.plzort = plzort
        self.date = date
        self.street = street
        self.lat = lat
        self.lon = lon
        self.radius = radius

    @staticmethod
    def get_token():
        """Fetch the dynamic token required for the second API call."""
        try:
            _LOGGER.info("Fetching token from API...")
            options = ChromeOptions()
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(options=options)
            driver.get(API_ENDPOINT)
            driver.implicitly_wait(10)

            script_content = None
            for request in driver.requests:
                if request.response:
                    if re.search(r"Pharmacy.*\.js", request.url):
                        script_content = gzip.decompress(request.response.body).decode(
                            "utf-8"
                        )
                        break

            driver.quit()
            if not script_content:
                raise ValueError("No script found in requests.")

            m = re.search(r"token:\"(?P<token>\w+)\"", script_content)
            if not m:
                raise ValueError("Token not found in response.")
            token = m.group("token")
            _LOGGER.info("Token fetched successfully.")
            return token
        except requests.RequestException as err:
            _LOGGER.error("Error fetching token: %s", err)
            raise

    def call_api(self):
        """Make a request to the API."""
        try:
            # Get the token
            token = self.get_token()

            # Make the second API request using the token and parameters
            _LOGGER.info("Fetching pharmacy data from API...")
            response = requests.get(
                url=API_ENDPOINT,
                params={
                    "tx_aponetpharmacy_search[action]": "result",
                    "tx_aponetpharmacy_search[controller]": "Search",
                    "tx_aponetpharmacy_search[search][plzort]": self.plzort,
                    "tx_aponetpharmacy_search[search][date]": self.date,
                    "tx_aponetpharmacy_search[search][street]": self.street,
                    "tx_aponetpharmacy_search[search][radius]": str(self.radius),
                    "tx_aponetpharmacy_search[search][lat]": str(self.lat),
                    "tx_aponetpharmacy_search[search][lng]": str(self.lon),
                    "tx_aponetpharmacy_search[token]": token,
                    "type": "1981",
                },
                timeout=10,
            )
            response.raise_for_status()

            return response

        except requests.RequestException as err:
            _LOGGER.error("Error fetching pharmacy data: %s", err)
            raise

    def get_data(self):
        """Parse response from the API."""
        try:
            response = self.call_api()

            data = response.json()
            _LOGGER.debug("Response from API: %s", data)

            # Process the pharmacy data
            apotheken = []
            for apotheke in (
                data.get("results", {}).get("apotheken", {}).get("apotheke", [])
            ):
                apotheken.append(Apotheke.from_source(apotheke))

            _LOGGER.info("Fetched %d pharmacies.", len(apotheken))
            return apotheken

        except JSONDecodeError as err:
            _LOGGER.error("Error decoding pharmacy data: %s", err)
            raise
