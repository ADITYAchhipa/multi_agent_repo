import pytest

pytestmark = pytest.mark.integration


def upload(client, text, key):
    return client.post(
        "/api/sources/upload",
        data={"source_type": "NOTES", "access_label": "PUBLIC_DEMO", "source_key": "history-test"},
        files={"file": ("note.txt", text.encode(), "text/plain")},
        headers={"Idempotency-Key": key},
    )


def test_source_current_and_historical_versions_beyond_first_page(proposal_system):
    client, _ = proposal_system
    for version in range(1, 102):
        response = upload(client, f"Revision {version}.", f"core-history-version-{version:04}")
        assert response.status_code == 202, response.text
        source_id = response.json()["source_id"]
        if version == 1:
            first = client.get(f"/api/sources/{source_id}").json()["version"]["id"]
    response = client.get(f"/api/sources/{source_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["versions"]) == 101
    assert body["version"]["id"] == body["source"]["current_version_id"]
    assert body["versions"][-1]["version"] == 101
    assert body["snippets"][0]["quote"] == "Revision 101."
    old = client.get(f"/api/sources/{source_id}", params={"version_id": first})
    assert old.status_code == 200, old.text
    assert old.json()["snippets"][0]["quote"] == "Revision 1."


def test_extracted_terms_are_queryable_and_receipt_verifies(proposal_system):
    client, _ = proposal_system
    response = upload(
        client, "Acme will deliver the API by 2026-12-01 for USD 1500.", "core-explicit-terms-0001"
    )
    assert response.status_code == 202, response.text
    items = client.get(
        "/api/promises", params={"deadline_from": "2026-12-01", "deadline_to": "2026-12-01"}
    ).json()["items"]
    assert len(items) == 1
    detail = client.get("/api/promises/" + items[0]["id"]).json()
    payload = detail["receipt"]["payload"]
    assert payload["deadline"]["local_date"] == "2026-12-01"
    assert payload["commercial_value"]["amount"] == "1500"
    verification = client.get("/api/promises/" + items[0]["id"] + "/verify")
    assert verification.status_code == 200, verification.text
    assert verification.json()["verification"]["integrity"] == "VALID"
