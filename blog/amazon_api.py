import os
from typing import Optional, Dict

# Minimal PA-API v5 wrapper. Avoids hard dependency if creds are missing.
# If you prefer the official SDK or python-amazon-paapi, swap this implementation.

import hashlib
import hmac
import json
import datetime

PAAPI_HOSTS = {
    "us-east-1": "webservices.amazon.com",
    "na": "webservices.amazon.com",
    "eu-west-1": "webservices.amazon.co.uk",
    "eu": "webservices.amazon.co.uk",
    "fe": "webservices.amazon.co.jp",
}


def _get_env(name: str) -> Optional[str]:
    v = os.getenv(name)
    return v.strip() if v else None


def _aws_v4_sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(key, dateStamp, regionName, serviceName):
    kDate = _aws_v4_sign(("AWS4" + key).encode("utf-8"), dateStamp)
    kRegion = hmac.new(kDate, regionName.encode("utf-8"), hashlib.sha256).digest()
    kService = hmac.new(kRegion, serviceName.encode("utf-8"), hashlib.sha256).digest()
    kSigning = hmac.new(kService, b"aws4_request", hashlib.sha256).digest()
    return kSigning


def _marketplace_for_host(host: str) -> str:
    if host.endswith("amazon.com"):
        return "www.amazon.com"
    if host.endswith("amazon.co.uk"):
        return "www.amazon.co.uk"
    if host.endswith("amazon.co.jp"):
        return "www.amazon.co.jp"
    return "www.amazon.com"


def _build_getitems_payload(asin: str, partner_tag: str, marketplace: str) -> Dict:
    return {
        "ItemIds": [asin],
        "Resources": [
            "Images.Primary.Medium",
            "Images.Primary.Large",
            "ItemInfo.Title",
        ],
        "PartnerTag": partner_tag,
        "PartnerType": "Associates",
        "Marketplace": marketplace,
    }


def fetch_paapi_images(asin: str, verbose: bool = False) -> Optional[Dict[str, str]]:
    # Lazy import to avoid hard failure if requests isn't installed yet
    try:
        import requests  # type: ignore
    except Exception:
        return None
    access_key = _get_env("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = _get_env("AMAZON_PAAPI_SECRET_KEY")
    partner_tag = _get_env("AMAZON_PAAPI_PARTNER_TAG")
    region = _get_env("AMAZON_PAAPI_REGION") or "us-east-1"

    if verbose:
        print(
            "PA-API env: ACCESS_KEY=%s, SECRET_KEY=%s, PARTNER_TAG=%s, REGION=%s"
            % (
                "set" if access_key else "missing",
                "set" if secret_key else "missing",
                partner_tag or "missing",
                region,
            )
        )

    if not (access_key and secret_key and partner_tag):
        if verbose:
            print("PA-API missing required credentials; skipping fetch")
        return None

    host = PAAPI_HOSTS.get(region, PAAPI_HOSTS["us-east-1"])
    endpoint = f"https://{host}/paapi5/getitems"

    amz_date = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    date_stamp = datetime.datetime.utcnow().strftime("%Y%m%d")

    marketplace = _marketplace_for_host(host)
    payload = _build_getitems_payload(asin, partner_tag, marketplace)
    payload_json = json.dumps(payload)

    service = "ProductAdvertisingAPI"
    method = "POST"
    canonical_uri = "/paapi5/getitems"
    canonical_querystring = ""
    content_type = "application/json; charset=UTF-8"
    target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems"
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:{target}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date;x-amz-target"
    canonical_request = (
        f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n{amz_date}\n{credential_scope}\n"
        + hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    )

    signing_key = _get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization_header = (
        f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "content-type": content_type,
        "x-amz-date": amz_date,
        "x-amz-target": target,
        "x-amz-content-sha256": payload_hash,
        "accept": "application/json",
        "Authorization": authorization_header,
    }

    if verbose:
        print(
            f"PA-API request: endpoint={endpoint}, marketplace={marketplace}, partner_tag={partner_tag}, asin={asin}"
        )

    try:
        resp = requests.post(endpoint, data=payload_json, headers=headers, timeout=10)
        if resp.status_code != 200:
            if verbose:
                try:
                    body = resp.text[:800]
                except Exception:
                    body = "<unreadable>"
                print(f"PA-API HTTP {resp.status_code} for {asin}: {body}")
            return None
        data = resp.json()
        if "Errors" in data and verbose:
            print(f"PA-API Errors for {asin}: {data.get('Errors')}")
        items = data.get("ItemsResult", {}).get("Items", [])
        if not items:
            if verbose:
                print(f"PA-API returned no items for {asin}. Raw: {data}")
            return None
        item = items[0]
        images = item.get("Images", {}).get("Primary", {})
        title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue")
        medium = images.get("Medium", {}).get("URL")
        large = images.get("Large", {}).get("URL")
        if not (medium or large):
            if verbose:
                print(f"PA-API item missing image URLs for {asin}. Item: {item}")
            return None
        return {
            "title": title,
            "image_url": medium or large,
            "image_url_2x": large or medium,
        }
    except Exception as e:
        if verbose:
            print(f"PA-API exception for {asin}: {e}")
        return None
