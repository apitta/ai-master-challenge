"""Cliente HTTP da API. A UI não acessa o banco: toda regra vive na camada de serviço."""

import os

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")


class ApiError(Exception):
    pass


@st.cache_resource
def _client() -> httpx.Client:
    return httpx.Client(base_url=API_URL, timeout=30)


def _request(method: str, path: str, **kwargs):
    try:
        response = _client().request(method, path, **kwargs)
    except httpx.TransportError as e:
        raise ApiError(f"API indisponível em {API_URL}. Ela pode estar iniciando; tente de novo em instantes.") from e
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = response.text
        raise ApiError(str(detail))
    return response.json()


@st.cache_data(ttl=300)
def filters() -> dict:
    return _request("GET", "/filters")


def opportunities(params: dict) -> list[dict]:
    return _request("GET", "/opportunities", params=params)


def summary(params: dict) -> dict:
    return _request("GET", "/summary", params=params)


def opportunity(opp_id: str) -> dict:
    return _request("GET", f"/opportunities/{opp_id}")


def run_command(opp_id: str, payload: dict) -> dict:
    return _request("POST", f"/opportunities/{opp_id}/commands", json=payload)
