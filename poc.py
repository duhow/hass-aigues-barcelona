#!/usr/bin/env python3
import requests
import os
import logging
import base64
import json

logging.basicConfig(level=logging.DEBUG)

user = os.getenv("AIGUA_USERNAME")
password = os.getenv("AIGUA_PASSWORD")

if all([not password, not user]):
    raise ValueError("Missing credentials")

class AiguesAPI:
    def __init__(self):
        self.cli = requests.Session()
        self.api_host = "https://api.aiguesdebarcelona.cat"
        # https://www.aiguesdebarcelona.cat/o/ofex-theme/js/chunk-vendors.e5935b72.js
        # https://www.aiguesdebarcelona.cat/o/ofex-theme/js/app.0499d168.js
        self.headers = {
            "Ocp-Apim-Subscription-Key": "3cca6060fee14bffa3450b19941bd954",
            "Ocp-Apim-Trace": "false",
        }

    def _generate_url(self, path, query) -> str:
        query_proc = ""
        if query:
            query_proc = "?" + "&".join([f"{k}={v}" for k, v in query.items()])
        return f"{self.api_host}/{path.lstrip('/')}{query_proc}"

    def _return_token_field(self, key):
        token = self.cli.cookies.get_dict().get("ofexTokenJwt")
        assert token, "Token login missing"

        data = token.split(".")[1]
        logging.debug(data)
        # add padding to avoid failures
        data = base64.urlsafe_b64decode(data + '==')

        return json.loads(data).get(key)

    def _query(self, path, query=None, json=None, headers=None, method="GET"):
        if headers is None:
            headers = dict()
        headers = {**self.headers, **headers}
        r = self.cli.request(
            method=method,
            url=self._generate_url(path, query),
            json=json,
            headers=headers
        )
        logging.debug(r.text)
        logging.debug(r.status_code)
        if r.status_code == 404:
            msg = r.text
            if len(r.text) > 5:
                msg = r.json().get("message", r.text)
            raise Exception(f"Not found: {msg}")
        if r.status_code == 401:
            msg = r.text
            if len(r.text) > 5:
                msg = r.json().get("message", r.text)
            raise Exception(f"Denied: {msg}")
        return r

    def login(self, user, password, recaptcha=None):
        # recaptcha seems to not be validated?
        if recaptcha is None:
            recaptcha = ""

        path = "/ofex-login-api/auth/getToken"
        query = {
            "lang": "ca",
            "recaptchaClientResponse": recaptcha
        }
        body = {
            "scope": "ofex",
            "companyIdentification": "",
            "userIdentification": user,
            "password": password
        }
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": "6a98b8b8c7b243cda682a43f09e6588b;product=portlet-login-ofex",
        }

        r = self._query(path, query, body, headers, method="POST")

        assert not r.json().get("errorMessage"), r.json().get("errorMessage")
        #{"errorMessage":"Los datos son incorrectos","result":false,"errorCode":"LOGIN_ERROR"}
        access_token = r.json().get("access_token")
        assert access_token, "Access token missing"

        # set as cookie: ofexTokenJwt
        # https://www.aiguesdebarcelona.cat/ca/area-clientes

    def profile(self, user=None):
        if user is None:
            user = self._return_token_field("name")

        path = "/ofex-login-api/auth/getProfile"
        query = {
            "lang": "ca",
            "userId": user,
            "clientId": user
        }
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
        query = {
            "lang": "ca",
            "userId": user,
            "clientId": user
        }
        for idx, stat in enumerate(status):
            query[f"assignationStatus[{str(idx)}]"] = stat.upper()

        r = self._query(path, query)

        data = r.json().get("data")
        return data
    


casa = AiguesAPI()
casa.login(user, password)
casa.contracts()
