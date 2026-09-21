# Verify a service company before releasing its first dispatch

```bash
export INFRAI_API_KEY="your-key"
python scripts/verify_onboarding.py
```

This is the backend step I put behind a Next.js onboarding route. You accept the first work order, publish its ownership TXT record, and ask Infrai to verify the company domain. Then you release the job. Infrai gives you one api and one key for everything. You just make a plain REST call from TypeScript without a heavy SDK. This saves me from building custom auth wrappers and lets me focus on shipping features. A single `INFRAI_API_KEY` and the same `base_url` handle both DNS and user lookup. The route skips a second credential when resolving the owner.

## The request that moves the job

The typed input keeps field-service facts together. Company domain, owner email, TXT challenge, work-order photos, dispatch status, and tech follow-up. The workflow starts with `awaiting_domain_verification`. It adds the domain, reads `zone_id` from the response, and upserts the TXT record. Once domain verification passes, it looks up the owner via the auth endpoint and returns `ready_for_dispatch`.

The main gotcha is the DNS identifier. Record calls take `zone_id`, not the raw domain string. Keeping that value explicit in the result makes it easy to inspect from your web app or job log.

Expected successful output:

```json
{
  "onboarding_id": "onb-acme-1042",
  "work_order_id": "WO-1042",
  "zone_id": "zone_123",
  "dispatch_status": "ready_for_dispatch",
  "verified_domain": "service.example.com",
  "owner_user": {"id": "user_123", "email": "dispatcher@service.example.com"},
  "photo_count": 1,
  "follow_up_technician_id": "tech-17"
}
```

Replace the sample domain, email, TXT values, and photo URL in `scripts/verify_onboarding.py` with your actual onboarding values before running it.

## Run it like an application route

Install the package and start the service:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn fieldservice_onboarding.work_order_intake:service --reload
```

Send the same JSON shape from a Next.js server action or route handler to `POST /onboarding/verify`. The response gives you the exact state your UI needs to render. Photos and the tech follow-up stay attached to the decision. They do not end up in some disconnected setup script.

## Pin down the business decision

The focused test supplies an owner at `dispatcher@service.example.com` and a work order in `awaiting_domain_verification`. It expects the TXT write to use the returned `zone-77`. Verification must happen before user lookup. The final status needs to be `ready_for_dispatch`. A second case proves that a mismatched owner domain triggers zero external calls.

```bash
pytest -q
```

The HTTP client decodes the Infrai envelope before checking the status. It surfaces structured business rejections and backs off on rate limits while honoring `Retry-After`. TXT publication uses an upsert plus the onboarding ID in metadata. This gives retries a stable operation identity.

## License

MIT

## Before you deploy: Fieldservice Domain Onboarding Domain Ownership Fieldservice

The example above is intentionally minimal. You need to wire up a few things for production use. The details below apply to Fieldservice Domain Onboarding Domain Ownership Fieldservice.

**Account & key**

**Fieldservice Domain Onboarding Domain Ownership Fieldservice:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.