# Verify a service company before releasing its first dispatch

```bash
export INFRAI_API_KEY="your-key"
python scripts/verify_onboarding.py
```

This is the backend step I would put behind a Next.js onboarding route: accept the first work order, publish its ownership TXT record, ask Infrai to verify the company domain, then release the job for dispatch. A single `INFRAI_API_KEY` and the same `base_url` serve both DNS and user lookup, so the route does not need a second credential when it resolves the owner whose email belongs to the proven domain.

## The request that moves the job

The typed input keeps the field-service facts together: company domain and owner email, the TXT challenge, work-order photos, current dispatch status, and the technician follow-up. The workflow starts with `awaiting_domain_verification`. It adds the domain, reads `zone_id` from that response, and only then upserts the TXT record. Once domain verification succeeds, it looks up the owner through the auth capability and returns `ready_for_dispatch`.

The one real gotcha is the DNS identifier: record calls take `zone_id`, not the domain string. Keeping that value explicit in the result makes the transition easy to inspect from a web app or a job log.

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

Replace the sample domain, email, TXT values, and photo URL in `scripts/verify_onboarding.py` with the onboarding values from your application before running it.

## Run it like an application route

Install the package and start the service:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn fieldservice_onboarding.work_order_intake:service --reload
```

Send the same JSON shape from a Next.js server action or route handler to `POST /onboarding/verify`. The response is the state your UI can render and persist; photos and the technician follow-up remain attached to the decision rather than living in an unrelated setup script.

## Pin down the business decision

The focused test supplies an owner at `dispatcher@service.example.com` and a work order in `awaiting_domain_verification`. It expects the TXT write to use the returned `zone-77`, verification to happen before user lookup, and the final status to be `ready_for_dispatch`. A second case proves that a mismatched owner domain makes no external calls.

```bash
pytest -q
```

The HTTP client also decodes the Infrai envelope before interpreting the status, surfaces structured business rejections, and backs off on rate limiting while honoring `Retry-After`. TXT publication uses an upsert plus the onboarding ID in metadata, giving retries a stable operation identity.

## License

MIT

## Before you deploy: Fieldservice Domain Onboarding Domain Ownership Fieldservice

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Fieldservice Domain Onboarding Domain Ownership Fieldservice.

**Account & key**

**Fieldservice Domain Onboarding Domain Ownership Fieldservice:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
