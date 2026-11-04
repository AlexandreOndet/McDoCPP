# Capturing GMA credentials (Phase 0)

Three paths, cheapest first. Prefer A; fall back to B, then C.

## Path A — guest token, no account, no proxy (try this first)

Public app trackers (mcbroken, hotnspicy) never log in. They mint an anonymous token with the app's hardcoded client credentials, then read menus. If the price menu accepts this token, no account or capture is ever needed; the collector mints a fresh token each run.

```
POST https://us-prod.api.mcd.com/v1/security/auth/token
  authorization: Basic base64("<clientid>:<secret>")
  mcd-clientid / mcd-clientsecret / mcd-sourceapp: GMA / mcd-marketid: CA / mcd-uuid: <uuid>
  content-type: application/x-www-form-urlencoded
  body: grantType=client_credentials
→ response.token
```

Set `MCD_CLIENT_ID` / `MCD_CLIENT_SECRET` from the app's client credentials (the US pair is published in the McReverse and mcbroken repos; never commit them). CA routes through `us-prod` with `mcd-marketid: CA`. No CA-specific id is public; if the mint 403s, CA needs its own, recoverable by static APK decompile.

Must run from a North-American IP: these endpoints region-lock with error `41600` otherwise. Verify the guest bearer against `GET /ca/gma/api/v1/restaurants/{id}/menus` before relying on it; if the price menu rejects a guest token, use Path B.

## Path B — magic-link login, no proxy (needs the disposable account)

`POST identity/email` → open the link from that inbox → `PUT /exp/v1/customer/activateandsignin` → ride `/login/refresh`. Public US/CA code does this with no Akamai sensor header. Persist the rotated refresh token after every call (both tokens rotate; access token lives ~15 min).

## Path C — device capture (fallback, needs a proxy)

Done once from a disposable McDonald's account on a real device, via mitmproxy (or Frida on a rooted/jailbroken phone). Only the refresh chain is kept afterwards; the password login needs the Akamai `x-acf-sensor-data` header and is never replayed by the collector. Magic-link login (Path B) avoids that header.

## What to capture (Path C)

Proxy the app, log in, then open any restaurant menu. From the flows, copy:

| Need | Where | Env var |
|---|---|---|
| `response.refreshToken` | body of `POST /exp/v1/customer/login` (or a later `/login/refresh`) | `MCD_REFRESH_TOKEN` |
| `mcd-clientid` request header | any request | `MCD_CLIENT_ID` |
| The rest of the request headers on `GET /ca/gma/api/v1/restaurants/{id}/menus` | see list below | `MCD_HEADERS_JSON` (JSON object) |

Headers to include in `MCD_HEADERS_JSON` (everything except `authorization`, `mcd-clientid`, `mcd-marketid`, `mcd-uuid`, which the code sets):

- `user-agent`
- `accept`, `accept-language`, `accept-encoding`, `content-type`
- `mcd-sourceapp`, `mcd-uuid-type` if present
- any `x-*` headers other than `x-acf-sensor-data` (drop that one)

Example:

```sh
export MCD_REFRESH_TOKEN='eyJ...'
export MCD_CLIENT_ID='9f3...'
export MCD_HEADERS_JSON='{"user-agent":"MCDSDK/23.2.0 (iPhone; 17.5; en-CA) GMA/9.x","accept":"application/json","accept-language":"en-CA","mcd-sourceapp":"GMA"}'
cd collector && uv run spike.py --store <restaurant_id> --save ../fixtures/captured/<id>.json
```

Also note, for `docs/STATUS.md`: the restaurant ID format you see in the menu URL (NSN vs numeric), the raw and gzipped payload size, and whether the refresh response contained a new `refreshToken` (rotation) or echoed the old one.

## Phase 0 checks the token enables

1. Refresh works without `x-acf-sensor-data` (spike prints "refresh ok").
2. Prices for 3 stores in 3 provinces match the app; keep one receipt photo.
3. `GET /exp/v1/restaurant/location?distance=&latitude=&longitude=&pageSize=&filter=summary` for the store sweep (`mcdocpp discover`).
4. Same requests from a GCP egress IP vs residential: compare status codes and any Akamai challenge body.
