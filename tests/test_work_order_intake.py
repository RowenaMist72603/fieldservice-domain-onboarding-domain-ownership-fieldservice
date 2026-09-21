from __future__ import annotations

import asyncio

import pytest

from fieldservice_onboarding.work_order_intake import OnboardingRequest, approve_dispatch


def intake(owner_email: str = "dispatcher@service.example.com") -> OnboardingRequest:
    return OnboardingRequest.model_validate(
        {
            "onboarding_id": "onb-1042",
            "company_domain": "service.example.com",
            "owner_email": owner_email,
            "txt_name": "_fieldservice-verification",
            "txt_content": "fieldservice-verification=onb-1042",
            "work_order_id": "WO-1042",
            "photos": [{"url": "https://images.example.com/panel.jpg", "caption": "Panel"}],
            "dispatch_status": "awaiting_domain_verification",
            "follow_up": {"technician_id": "tech-17", "note": "Check label"},
        }
    )


class RecordingAPI:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    async def add_domain(self, domain: str, onboarding_id: str) -> dict[str, object]:
        self.calls.append(("add", domain, onboarding_id))
        return {"zone_id": "zone-77"}

    async def upsert_txt(self, zone_id: str, name: str, content: str, onboarding_id: str) -> dict[str, object]:
        self.calls.append(("txt", zone_id, name, content, onboarding_id))
        return {"record_id": "record-8"}

    async def verify_domain(self, domain: str) -> dict[str, object]:
        self.calls.append(("verify", domain))
        return {"domain": domain}

    async def get_user_by_email(self, email: str) -> dict[str, object]:
        self.calls.append(("user", email))
        return {"id": "user-9", "email": email}


def test_verified_domain_releases_work_order_for_dispatch() -> None:
    api = RecordingAPI()
    result = asyncio.run(approve_dispatch(intake(), api))

    assert result.dispatch_status == "ready_for_dispatch"
    assert result.zone_id == "zone-77"
    assert result.photo_count == 1
    assert api.calls == [
        ("add", "service.example.com", "onb-1042"),
        ("txt", "zone-77", "_fieldservice-verification", "fieldservice-verification=onb-1042", "onb-1042"),
        ("verify", "service.example.com"),
        ("user", "dispatcher@service.example.com"),
    ]


def test_owner_email_must_match_the_proven_company_domain() -> None:
    api = RecordingAPI()
    with pytest.raises(ValueError, match="owner_email must belong"):
        asyncio.run(approve_dispatch(intake("dispatcher@other.example"), api))
    assert api.calls == []
