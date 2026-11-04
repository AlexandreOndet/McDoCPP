# Capturing GMA credentials (Phase 0)

Done once from a disposable McDonald's account on a real device, via mitmproxy (or Frida on a rooted/jailbroken phone). Only the refresh chain is kept afterwards; the login itself needs the Akamai `x-acf-sensor-data` header and is never replayed by the collector.

## What to capture

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
