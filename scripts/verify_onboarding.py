from __future__ import annotations

import asyncio
import json
import os

from fieldservice_onboarding.infrai_client import InfraiClient
from fieldservice_onboarding.work_order_intake import OnboardingRequest, approve_dispatch


async def main() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise SystemExit("Set INFRAI_API_KEY before running this script")

    request = OnboardingRequest.model_validate(
        {
            "onboarding_id": "onb-acme-1042",
            "company_domain": "service.example.com",
            "owner_email": "dispatcher@service.example.com",
            "txt_name": "_fieldservice-verification",
            "txt_content": "fieldservice-verification=onb-acme-1042",
            "work_order_id": "WO-1042",
            "photos": [
                {
                    "url": "https://images.example.com/work-orders/WO-1042-panel.jpg",
                    "caption": "Electrical panel before service",
                }
            ],
            "dispatch_status": "awaiting_domain_verification",
            "follow_up": {
                "technician_id": "tech-17",
                "note": "Confirm panel label after arrival",
            },
        }
    )
    async with InfraiClient(api_key) as client:
        result = await approve_dispatch(request, client)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

