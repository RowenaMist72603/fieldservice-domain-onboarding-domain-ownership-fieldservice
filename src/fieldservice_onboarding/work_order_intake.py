from __future__ import annotations

import os
from typing import Literal, Protocol

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from .infrai_client import InfraiClient, InfraiError


class WorkOrderPhoto(BaseModel):
    url: HttpUrl
    caption: str = Field(min_length=1, max_length=160)


class TechnicianFollowUp(BaseModel):
    technician_id: str = Field(min_length=1)
    note: str = Field(min_length=1, max_length=500)


class OnboardingRequest(BaseModel):
    onboarding_id: str = Field(min_length=1)
    company_domain: str = Field(min_length=3)
    owner_email: str = Field(pattern=r"^[^@]+@[^@]+$")
    txt_name: str = Field(min_length=1)
    txt_content: str = Field(min_length=1)
    work_order_id: str = Field(min_length=1)
    photos: list[WorkOrderPhoto] = Field(min_length=1)
    dispatch_status: Literal["awaiting_domain_verification"]
    follow_up: TechnicianFollowUp


class OnboardingResult(BaseModel):
    onboarding_id: str
    work_order_id: str
    zone_id: str
    dispatch_status: Literal["ready_for_dispatch"]
    verified_domain: str
    owner_user: dict[str, object]
    photo_count: int
    follow_up_technician_id: str


class OnboardingAPI(Protocol):
    async def add_domain(
        self, domain: str, onboarding_id: str
    ) -> dict[str, object]:
        raise AssertionError("protocol method")

    async def upsert_txt(
        self, zone_id: str, name: str, content: str, onboarding_id: str
    ) -> dict[str, object]:
        raise AssertionError("protocol method")

    async def verify_domain(self, domain: str) -> dict[str, object]:
        raise AssertionError("protocol method")

    async def get_user_by_email(self, email: str) -> dict[str, object]:
        raise AssertionError("protocol method")


async def approve_dispatch(
    request: OnboardingRequest, client: OnboardingAPI
) -> OnboardingResult:
    email_domain = request.owner_email.rsplit("@", 1)[1].lower()
    if email_domain != request.company_domain.lower():
        raise ValueError("owner_email must belong to company_domain")

    domain = await client.add_domain(request.company_domain, request.onboarding_id)
    zone_id = domain.get("zone_id")
    if not isinstance(zone_id, str) or not zone_id:
        raise RuntimeError("domain response did not include zone_id")

    await client.upsert_txt(
        zone_id,
        request.txt_name,
        request.txt_content,
        request.onboarding_id,
    )
    await client.verify_domain(request.company_domain)
    owner = await client.get_user_by_email(request.owner_email)

    return OnboardingResult(
        onboarding_id=request.onboarding_id,
        work_order_id=request.work_order_id,
        zone_id=zone_id,
        dispatch_status="ready_for_dispatch",
        verified_domain=request.company_domain,
        owner_user=owner,
        photo_count=len(request.photos),
        follow_up_technician_id=request.follow_up.technician_id,
    )


service = FastAPI(title="Field-service domain onboarding")


@service.post("/onboarding/verify", response_model=OnboardingResult)
async def verify_onboarding(request: OnboardingRequest) -> OnboardingResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="INFRAI_API_KEY is required")

    try:
        async with InfraiClient(api_key) as client:
            return await approve_dispatch(request, client)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except InfraiError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "error": error.detail},
        ) from error
