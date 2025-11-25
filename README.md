# Automated Order Management System

This repository now includes a small **HAPI FHIR Python demo** that shows how to connect to the public `hapi.fhir.org` server, search for patients, and list their associated documentation. It is intended as a starting point for experimenting with the FHIR REST API.

## Prerequisites

- Python 3.10+
- The demo uses only the Python standard library. A virtual environment is recommended but no third-party packages are required.

## Running the demo

The script is located at `demos/hapi_fhir_demo.py`. By default it targets the public R4 endpoint at `https://hapi.fhir.org/baseR4`.

### Quick start (works in VS Code or any terminal)

1. Ensure Python 3.10+ is available on your machine.
2. Open a terminal (VS Code "Terminal" tab is fine) in the repository root.
3. (Optional) Create and activate a virtual environment: `python -m venv .venv && source .venv/bin/activate`.
4. Run a search for patients and their documents. For example, find up to three patients named "Peter" and fetch up to two documents for each:

   ```bash
   python demos/hapi_fhir_demo.py --given Peter --patient-count 3 --document-count 2
   ```

   This will:

   - search `hapi.fhir.org/baseR4` for patients whose given name matches "Peter",
   - print each matching patient's basic demographics and ID, and
   - request up to two `DocumentReference` resources per patient, printing attachment URLs and a 200-byte preview when available.

5. Review the printed output. Each patient block is followed by their `DocumentReference` resources. When a document contains an attachment URL, the script downloads the payload and prints the first 200 bytes so you can confirm the end-to-end path.

If you prefer a different interface, the same command works in PowerShell, Git Bash, or macOS/Linux terminals.

### Additional options

- `--family` – filter by family name.
- `--base-url` – point to another HAPI FHIR instance.
- `--patient-count` – limit how many patients to return (default 3).
- `--document-count` – limit how many DocumentReference resources are fetched per patient (default 5).
- `--resource-path` – fetch a single resource and pretty-print its JSON payload instead of running the patient/document search. For example:

  ```bash
  # Fetch a specific Observation
  python demos/hapi_fhir_demo.py --resource-path Observation/123

  # Search Observation resources by code system/value
  python demos/hapi_fhir_demo.py --resource-path "Observation?code=http://loinc.org|789-8"
  ```

  Combine with `--base-url` if you want to hit a different FHIR server.

### Troubleshooting connectivity

- The public demo endpoint occasionally rate limits or returns HTTP 403/429 responses when behind strict proxies. Re-run the command after a short pause or try from a network without outbound restrictions.
- To verify basic connectivity, start with a small query such as `python demos/hapi_fhir_demo.py --patient-count 1` and look for any error messages reported by the script.
