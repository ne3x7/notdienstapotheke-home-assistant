from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional

import requests
import re
from datetime import datetime
import logging

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
            datetime_from=datetime.strptime(result["startdatum"] + " " + result["startzeit"], '%d.%m.%Y %H:%M'),
            datetime_to=datetime.strptime(result["enddatum"] + " " + result["endzeit"], '%d.%m.%Y %H:%M'),
        )

    def to_dict(self) -> dict:
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

    @staticmethod
    def get_token():
        """Fetch the dynamic token required for the second API call."""
        try:
            _LOGGER.info("Fetching token from API...")
            r = requests.get("/_assets/vite/assets/Pharmacymap-DnwNJfmO.js")
            r.raise_for_status()
            m = re.search(r"token:\"(?P<token>\w+)\"", r.text)
            if not m:
                raise ValueError("Token not found in response.")
            token = m.group("token")
            _LOGGER.info("Token fetched successfully.")
            return token
        except requests.RequestException as err:
            _LOGGER.error(f"Error fetching token: {err}")
            raise

    def get_data(self, plzort: str, date: Optional[str], street: Optional[str], lat: Optional[float], lon: Optional[float], radius: Optional[int]=5):
        """Fetch pharmacy data from the API."""
        try:
            # Get the token
            token = self.get_token()

            # Make the second API request using the token and parameters
            _LOGGER.info("Fetching pharmacy data from API...")
            response = requests.get(
                url=f"{API_ENDPOINT}/apotheke/notdienstsuche",
                params={
                    "tx_aponetpharmacy_search[action]": "result",
                    "tx_aponetpharmacy_search[controller]": "Search",
                    "tx_aponetpharmacy_search[search][plzort]": plzort,
                    "tx_aponetpharmacy_search[search][date]": date,
                    "tx_aponetpharmacy_search[search][street]": street,
                    "tx_aponetpharmacy_search[search][radius]": str(radius),
                    "tx_aponetpharmacy_search[search][lat]": str(lat),
                    "tx_aponetpharmacy_search[search][lng]": str(lon),
                    "tx_aponetpharmacy_search[token]": token,
                    "type": "1981"
                }
            )
            response.raise_for_status()

            data = response.json()
            _LOGGER.debug(f"Response from API: {data}")

            # Process the pharmacy data
            apotheken = []
            for apotheke in data.get('results', {}).get('apotheken', {}).get('apotheke', []):
                apotheken.append(Apotheke.from_source(apotheke))

            _LOGGER.info(f"Fetched {len(apotheken)} pharmacies.")
            return apotheken

        except requests.RequestException as err:
            _LOGGER.error(f"Error fetching pharmacy data: {err}")
            raise

