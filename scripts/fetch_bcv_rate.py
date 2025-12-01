#!/usr/bin/env python3
"""Fetch the official USD rate from the BCV website and write `tasa.json`.

The script tries to locate numeric patterns near keywords like "Dólar" or "Tasa"
in the BCV homepage text. It's intentionally tolerant to different number formats
(thousands separator '.' or ',' and decimal separator '.' or ',').
"""
import re
import json
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
import os

# Use certifi's CA bundle when available to avoid Windows Python SSL issues
try:
    import certifi
    _VERIFY = certifi.where()
    # Also set environment vars so OpenSSL / requests pick it up reliably on Windows
    os.environ.setdefault("REQUESTS_CA_BUNDLE", _VERIFY)
    os.environ.setdefault("SSL_CERT_FILE", _VERIFY)
except Exception:
    certifi = None
    _VERIFY = True

URL = "https://www.bcv.org.ve/"


def normalize_number(s: str):
    s = s.strip()
    s = re.sub(r"[^0-9.,]", "", s)
    if not s:
        return None
    # If both '.' and ',' exist, decide which is decimal:
    if '.' in s and ',' in s:
        if s.find('.') < s.find(','):
            # '.' thousands, ',' decimal
            s = s.replace('.', '').replace(',', '.')
        else:
            # ',' thousands, '.' decimal
            s = s.replace(',', '')
    else:
        # Only comma -> decimal, Only dot -> decimal or plain
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    try:
        return float(s)
    except Exception:
        return None


def find_rate(text: str):
    # Try some keyword-based regexes first
    patterns = [
        r"(?:D[oó]lar|USD)[^0-9\-\n\r]{0,20}([0-9\.,]+)",
        r"Tasa(?: de cambio)?[^0-9\-\n\r]{0,20}([0-9\.,]+)",
        r"Oficial[^0-9\-\n\r]{0,20}([0-9\.,]+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            val = normalize_number(m.group(1))
            if val is not None:
                return val

    # Fallback: pick the last reasonable-looking number > 1
    nums = re.findall(r"([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]+)?)", text)
    candidates = []
    for n in nums:
        v = normalize_number(n)
        if v is not None and v > 1:
            candidates.append(v)
    if candidates:
        return candidates[-1]
    return None


def main():
    ssl_unverified = False
    try:
        print(f"Usando verify={_VERIFY}")
        resp = requests.get(URL, timeout=20, verify=_VERIFY)
        resp.raise_for_status()
    except requests.exceptions.SSLError as e:
        print("Error SSL al conectar con el BCV:", e, file=sys.stderr)
        if certifi is None:
            print("Sugerencia: instale 'certifi' (pip install certifi) o 'certifi-win32' en Windows.", file=sys.stderr)
            print("También puede exportar SSL_CERT_FILE/REQUESTS_CA_BUNDLE apuntando al bundle de CA.", file=sys.stderr)
        else:
            print("Se detectó 'certifi', pero la verificación SSL falló. Intente instalar 'certifi-win32' o actualizar su store de certificados.", file=sys.stderr)

        # Como último recurso para entornos CI (GitHub Actions), podemos reintentar
        # desactivando la verificación SSL. Esto NO es recomendable en entornos
        # locales/producción, pero permite que el workflow continúe si el host
        # remoto tiene problemas en la cadena de certificados.
        is_ci = os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true"
        if is_ci:
            print("Entorno CI detectado: reintentando la petición con verify=False (NO recomendado).", file=sys.stderr)
            try:
                resp = requests.get(URL, timeout=20, verify=False)
                resp.raise_for_status()
                ssl_unverified = True
            except Exception as e2:
                print("Reintento sin verificación SSL falló:", e2, file=sys.stderr)
                sys.exit(1)
        else:
            sys.exit(1)
    except Exception as e:
        print("Error fetching BCV site:", e, file=sys.stderr)
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "lxml")
    text = soup.get_text(" ", strip=True)
    rate = find_rate(text)

    if rate is None:
        print("No se encontró la tasa en la página del BCV.", file=sys.stderr)
        sys.exit(2)

    now = datetime.now(timezone.utc)
    data = {
        "date": now.strftime("%Y-%m-%d"),
        "rate": rate,
        "source": URL,
        "fetched_at": now.isoformat(),
    }

    with open("tasa.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("tasa.json escrito:", data)


if __name__ == "__main__":
    main()
