import base64
import datetime
import json
import logging

import requests

from .const import API_COOKIE_TOKEN
from .const import API_HOST

TIMEOUT = 60

_LOGGER: logging.Logger = logging.getLogger(__name__)


class AiguesApiClient:
    def __init__(
        self, username, password, contract=None, session: requests.Session = None
    ):
        if session is None:
            session = requests.Session()
        self.cli = session
        self.api_host = f"https://{API_HOST}"
        # https://www.aiguesdebarcelona.cat/o/ofex-theme/js/chunk-vendors.e5935b72.js
        # https://www.aiguesdebarcelona.cat/o/ofex-theme/js/app.0499d168.js
        self.headers = {
            "Ocp-Apim-Subscription-Key": "3cca6060fee14bffa3450b19941bd954",
            "Ocp-Apim-Trace": "false",
            "Content-Type": "application/json; charset=UTF-8",
        }
        self._username = username
        self._password = password
        self._contract = contract
        self.last_response = None

    def _generate_url(self, path, query) -> str:
        query_proc = ""
        if query:
            query_proc = "?" + "&".join([f"{k}={v}" for k, v in query.items()])
        return f"{self.api_host}/{path.lstrip('/')}{query_proc}"

    def _return_token_field(self, key):
        token = self.cli.cookies.get_dict().get(API_COOKIE_TOKEN)
        if not token:
            _LOGGER.warning("Token login missing")
            return False

        data = token.split(".")[1]
        _LOGGER.debug(data)
        # add padding to avoid failures
        data = base64.urlsafe_b64decode(data + "==")

        return json.loads(data).get(key)

    def _query(self, path, query=None, json=None, headers=None, method="GET"):
        if headers is None:
            headers = dict()
        headers = {**self.headers, **headers}

        resp = self.cli.request(
            method=method,
            url=self._generate_url(path, query),
            json=json,
            headers=headers,
            timeout=TIMEOUT,
        )
        _LOGGER.debug(f"Query done with code {resp.status_code}")
        msg = resp.text
        self.last_response = resp.text
        if len(msg) > 5 and (msg.startswith("{") or msg.startswith("[")):
            msg = resp.json()
            if isinstance(msg, list) and len(msg) == 1:
                msg = msg[0]
            self.last_response = msg.copy()
            msg = msg.get("message", resp.text)

        if resp.status_code == 500:
            raise Exception(f"Server error: {msg}")
        if resp.status_code == 404:
            raise Exception(f"Not found: {msg}")
        if resp.status_code == 401:
            raise Exception(f"Denied: {msg}")
        if resp.status_code == 400:
            raise Exception(f"Bad response: {msg}")

        return resp

    def login(self, user=None, password=None, recaptcha=None):
        if user is None:
            user = self._username
        if password is None:
            password = self._password
        # recaptcha seems to not be validated?
        if recaptcha is None:
            recaptcha = ""

        path = "/ofex-login-api/auth/getToken"
        query = {"lang": "ca", "recaptchaClientResponse": recaptcha}
        body = {
            "scope": "ofex",
            "companyIdentification": "",
            "userIdentification": user,
            "password": password,
        }
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": "6a98b8b8c7b243cda682a43f09e6588b;product=portlet-login-ofex",
        }

        r = self._query(path, query, body, headers, method="POST")

        _LOGGER.debug(r)
        error = r.json().get("errorMessage", None)
        if error:
            _LOGGER.warning(error)
            return False

        access_token = r.json().get("access_token", None)
        if not access_token:
            _LOGGER.warning("Access token missing")
            return False

        return True

        # set as cookie: ofexTokenJwt
        # https://www.aiguesdebarcelona.cat/ca/area-clientes

    def set_token(self, token: str):
        host = ".".join(self.api_host.split(".")[1:])
        cookie_data = {
            "name": API_COOKIE_TOKEN,
            "value": token,
            "domain": f".{host}",
            "path": "/",
            "secure": True,
            "rest": {"HttpOnly": True, "SameSite": "None"},
        }
        cookie = requests.cookies.create_cookie(**cookie_data)
        return self.cli.cookies.set_cookie(cookie)

    def profile(self, user=None):
        if user is None:
            user = self._return_token_field("name")

        path = "/ofex-login-api/auth/getProfile"
        query = {"lang": "ca", "userId": user, "clientId": user}
        headers = {
            "Ocp-Apim-Subscription-Key": "6a98b8b8c7b243cda682a43f09e6588b;product=portlet-login-ofex"
        }

        r = self._query(path, query, headers=headers, method="POST")

        assert r.json().get("user_data"), "User data missing"
        return r.json()

    def contracts(self, user=None, status=["ASSIGNED", "PENDING"]):
        if user is None:
            user = self._return_token_field("name")
        if isinstance(status, str):
            status = [status]

        path = "/ofex-contracts-api/contracts"
        query = {"lang": "ca", "userId": user, "clientId": user}
        for idx, stat in enumerate(status):
            query[f"assignationStatus[{str(idx)}]"] = stat.upper()

        r = self._query(path, query)

        data = r.json().get("data")
        return data

    @property
    def contract_id(self):
        return [x["contractDetail"]["contractNumber"] for x in self.contracts()]

    @property
    def first_contract(self):
        contract_ids = self.contract_id
        assert (
            len(contract_ids) == 1
        ), "Provide a Contract ID to retrieve specific invoices"
        return contract_ids[0]

    def invoices(self, contract=None, user=None, last_months=36, mode="ALL"):
        if user is None:
            user = self._return_token_field("name")
        if contract is None:
            contract = self.first_contract

        path = "/ofex-invoices-api/invoices"
        query = {
            "contractNumber": contract,
            "userId": user,
            "clientId": user,
            "lang": "ca",
            "lastMonths": last_months,
            "mode": mode,
        }

        r = self._query(path, query)

        data = r.json().get("data")
        return data

    def invoices_debt(self, contract=None, user=None):
        return self.invoices(contract, user, last_months=0, mode="DEBT")

    def consumptions(
        self, date_from, date_to=None, contract=None, user=None, frequency="HOURLY"
    ):
        if user is None:
            user = self._return_token_field("name")
        if contract is None:
            contract = self.first_contract
        if frequency not in ["HOURLY", "DAILY"]:
            raise ValueError(f"Invalid {frequency=}")

        if date_to is None:
            date_to = date_from + datetime.timedelta(days=1)
        if isinstance(date_from, datetime.date):
            date_from = date_from.strftime("%d-%m-%Y")
        if isinstance(date_to, datetime.date):
            date_to = date_to.strftime("%d-%m-%Y")

        path = "/ofex-water-consumptions-api/meter/consumptions"
        query = {
            "consumptionFrequency": frequency,
            "contractNumber": contract,
            "clientId": user,
            "userId": user,
            "lang": "ca",
            "fromDate": date_from,
            "toDate": date_to,
            "showNegativeValues": "false",
        }

        r = self._query(path, query)

        data = r.json().get("data")
        return data

    def consumptions_week(self, date_from: datetime.date, contract=None, user=None):
        if date_from is None:
            date_from = datetime.datetime.now()
        # get first day of week
        monday = date_from - datetime.timedelta(days=date_from.weekday())
        sunday = monday + datetime.timedelta(days=6)
        return self.consumptions(monday, sunday, contract, user, frequency="DAILY")

    def consumptions_month(self, date_from: datetime.date, contract=None, user=None):
        first = date_from.replace(day=1)
        next_month = date_from.replace(day=28) + datetime.timedelta(days=4)
        last = next_month - datetime.timedelta(days=next_month.day)
        return self.consumptions(first, last, contract, user, frequency="DAILY")

    def parse_consumptions(self, info, key="accumulatedConsumption"):
        return [x[key] for x in info]
