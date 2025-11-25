"""Simple technical demo to interact with a public HAPI FHIR server.

The script searches for a patient, prints basic demographics, and then
retrieves any DocumentReference resources associated with that patient.
Attachments referenced from DocumentReferences are fetched when a URL is
available so we can preview the start of the payload.
"""
from __future__ import annotations

import argparse
import json
from typing import Iterable, List, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def build_url(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def fetch_resource(url: str, params: dict | None = None) -> dict:
    query = urlencode(params or {})
    full_url = f"{url}?{query}" if query else url
    request = Request(full_url)
    try:
        with urlopen(request, timeout=15) as response:
            payload = response.read()
    except Exception as exc:  # noqa: BLE001 - broad to surface network failures cleanly
        raise RuntimeError(f"Failed to GET {full_url}: {exc}") from exc
    return json.loads(payload)


def search_patients(base_url: str, given: str | None, family: str | None, count: int) -> List[dict]:
    params = {"_count": count}
    if given:
        params["given"] = given
    if family:
        params["family"] = family

    bundle = fetch_resource(build_url(base_url, "Patient"), params=params)
    return [entry["resource"] for entry in bundle.get("entry", []) if entry.get("resource")]


def summarize_patient(patient: dict) -> str:
    names = [
        " ".join(filter(None, [n.get("given", [None])[0], n.get("family")]))
        for n in patient.get("name", [])
    ]
    identifiers = [f"{i.get('system', '')}|{i.get('value', '')}" for i in patient.get("identifier", [])]
    addresses = [", ".join(filter(None, [a.get("city"), a.get("state"), a.get("country")])) for a in patient.get("address", [])]

    lines = [
        f"ID: {patient.get('id', 'unknown')}",
        f"Names: {', '.join(names) or 'N/A'}",
        f"Gender: {patient.get('gender', 'N/A')}",
        f"Birth date: {patient.get('birthDate', 'N/A')}",
        f"Identifiers: {', '.join(identifiers) or 'N/A'}",
        f"Addresses: {', '.join(addresses) or 'N/A'}",
    ]
    return "\n".join(lines)


def fetch_document_references(base_url: str, patient_id: str, count: int) -> List[dict]:
    params = {"subject": f"Patient/{patient_id}", "_count": count}
    bundle = fetch_resource(build_url(base_url, "DocumentReference"), params=params)
    return [entry["resource"] for entry in bundle.get("entry", []) if entry.get("resource")]


def preview_attachment(base_url: str, attachment: dict) -> Tuple[str, str]:
    url = attachment.get("url")
    if not url:
        return ("No URL", "")

    full_url = build_url(base_url, url)
    request = Request(full_url)
    try:
        with urlopen(request, timeout=15) as response:
            payload = response.read()
    except Exception as exc:  # noqa: BLE001
        return (full_url, f"Error fetching attachment: {exc}")

    preview = payload[:200]
    try:
        preview_text = preview.decode("utf-8")
    except UnicodeDecodeError:
        preview_text = preview.hex()

    return (full_url, preview_text)


def display_document_references(base_url: str, documents: Iterable[dict]) -> str:
    if not documents:
        return "No documents found."

    blocks = []
    for doc in documents:
        header = [
            f"DocumentReference/{doc.get('id', 'unknown')}",
            f"Status: {doc.get('status', 'N/A')}",
            f"Type: {doc.get('type', {}).get('text', 'N/A')}",
            f"Category: {', '.join([c.get('text', '') for c in doc.get('category', [])]) or 'N/A'}",
            f"Date: {doc.get('date', 'N/A')}",
        ]

        attachments = []
        for content in doc.get("content", []):
            attachment = content.get("attachment", {})
            url, preview = preview_attachment(base_url, attachment)
            attachments.append(
                "\n".join(
                    [
                        f"  - Attachment contentType: {attachment.get('contentType', 'N/A')}",
                        f"    URL: {url}",
                        f"    Preview (first 200 bytes): {preview}",
                    ]
                )
            )

        block = "\n".join(header + attachments)
        blocks.append(block)

    return "\n\n".join(blocks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HAPI FHIR patient/document demo")
    parser.add_argument("--base-url", default="https://hapi.fhir.org/baseR4", help="FHIR base URL")
    parser.add_argument(
        "--resource-path",
        help="Fetch a specific resource path (e.g., Observation/123) and print it as JSON",
    )
    parser.add_argument("--given", help="Patient given name to search")
    parser.add_argument("--family", help="Patient family name to search")
    parser.add_argument("--patient-count", type=int, default=3, help="Number of matching patients to return")
    parser.add_argument("--document-count", type=int, default=5, help="Number of documents per patient to fetch")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.resource_path:
        url = build_url(args.base_url, args.resource_path)
        resource = fetch_resource(url)
        print(json.dumps(resource, indent=2))
        return

    print(f"Searching {args.base_url} for patients...")
    patients = search_patients(args.base_url, args.given, args.family, args.patient_count)
    if not patients:
        print("No patients found with provided criteria.")
        return

    for patient in patients:
        print("\n== Patient ==")
        print(summarize_patient(patient))

        patient_id = patient.get("id")
        if not patient_id:
            print("Skipping documents because patient has no id.")
            continue

        print("\n-- Documents --")
        documents = fetch_document_references(args.base_url, patient_id, args.document_count)
        print(display_document_references(args.base_url, documents))


if __name__ == "__main__":
    main()
