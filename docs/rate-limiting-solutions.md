# Rate Limiting: Problem Analysis and Solutions

**Reference:** product-backlog#1716
**Date:** 2026-04-10
**Author:** Santiago Regusci

---

## Problem Statement

Bio raised concerns about rate limiting when many users simultaneously access articles with hundreds of annotations. Investigation revealed a compounding set of issues beyond Bio's specific case.

### How Bio Actually Uses the API

Bio does **not** use the badge endpoint. They call the **search API** (`/api/search`) — hitting the general `/api` rate limit — to get annotation counts and data. They use the versioning feature (Karen's work in #10078/#10093) to query specific article versions via the `uri` parameter with version suffixes (e.g., `uri=https://example.com/article:v1:v2`).

Their actual request pattern per page load (observed via browser network tab on medrxiv.org):

```
# Call per group — same query, different group IDs (e.g., ApM1XL6A, PyEqGn2e)
GET /api/search?limit=50&sort=created&order=asc&_separate_replies=false
    &group=ApM1XL6A
    &uri=https://www.medrxiv.org/content/10.64898/2025.12.31.25343212v1:v0:v1
    &uri=doi:10.64898/2025.12.31.25343212:v0:v1
```

Key details:
- **2 groups queried per page** (separate review channels — e.g., TRIP Peer Reviews, Community Reviews)
- **`limit=50`** per request — for articles with many annotations, they paginate
- **`:v0:v1`** suffix — queries both unversioned and v1 annotations in one call
- **Two `uri` params** — full URL + DOI, catching annotations made against either
- **Client-side, unauthenticated** — browser requests from medrxiv.org, no auth token
- **Full annotation bodies returned** — used to render the "Reviews and Context" sidebar

**Pagination multiplier:** For an article with 500 annotations in one group at `limit=50`, that's 10 paginated calls per group. With 2 groups: **up to 20 calls per user per page load**.

This means the relevant rate limit for Bio is:

| Endpoint | Rate | Burst | Mode |
|---|---|---|---|
| General `/api` (includes `/api/search`) | 4 req/s | 44 | nodelay |
| `/api/badge` | 1 req/s | 15 | delay |
| `POST /api/annotations` | 4 req/s | 8 | delay |

### Shared-IP Scenario (Conference, University, Corporate)

For unauthenticated requests (Bio's group is world-readable, they don't want to expose tokens in client code), rate limiting keys on `CF-Connecting-IP` (the end user's real IP via CloudFlare). When users share an IP (NAT), they share a rate limit bucket.

**Conference example — lightly annotated article (few annotations, no pagination):**
200 people on same WiFi, each triggers 2 search API calls (1 per group):
- 400 requests from one IP to `/api/search`
- Burst allows 44 instant (nodelay), then 4/s sustained
- Remaining 356 requests take **~89 seconds** to drain

**Conference example — heavily annotated article (500 annotations in one group):**
200 people on same WiFi, each triggers up to 20 paginated calls (10 pages × 2 groups):
- **4,000 requests** from one IP to `/api/search`
- Burst allows 44 instant, then 4/s sustained
- Remaining 3,956 requests take **~16.5 minutes** to drain
- Most users see `429 Too Many Requests` for extended periods

This isn't Bio-specific. Any shared-IP environment (university lecture halls, corporate offices, conference WiFi) can trigger this.

### Monitoring Gap

We have **zero visibility** into rate limiting events today:
- `access_log off` in nginx — no request logging
- 429 responses are returned by nginx before reaching gunicorn — New Relic's Python agent never sees them
- No alerting, no dashboards, no way to know if users are being rate-limited right now

---

## Current Architecture

```
User -> CloudFlare -> nginx (rate limiting here) -> gunicorn -> Pyramid app
                              |
                              +-- 429 returned here, never reaches app
```

**Infrastructure in play:**
- CloudFlare (CDN/proxy, provides `CF-Connecting-IP`)
- nginx (rate limiting via `limit_req_zone`, in-memory per-worker)
- PostgreSQL, Elasticsearch, RabbitMQ (no Redis currently)
- New Relic (Python agent for web/worker, not for nginx)
- Alpine Linux Docker containers

**Rate limit key logic** (`conf/nginx.conf:29-32`):
```nginx
map $http_authorization $limit_per_user {
  "" $http_cf_connecting_ip;    # unauthenticated: key by IP
  default $http_authorization;  # authenticated: key by token
}
```

---

## Solutions

### Solution 1: Increase nginx Rate Limits (Quick Win)

**What:** Raise the badge endpoint limits and general API limits.

**Changes to `conf/nginx.conf`:**
```nginx
# Current
limit_req_zone $limit_per_user zone=badge_user_limit:1m rate=1r/s;
limit_req zone=badge_user_limit burst=15;

# Proposed
limit_req_zone $limit_per_user zone=badge_user_limit:2m rate=10r/s;
limit_req zone=badge_user_limit burst=100 nodelay;
```

**Pros:**
- Minimal change, deploy in minutes
- No new infrastructure
- Conference scenario: 600 requests with burst=100 + 10/s clears in ~50 seconds instead of ~10 minutes

**Cons:**
- Still shared-memory, per-worker — not shared across nginx workers or pods
- A single bad actor from one IP gets more headroom too
- Doesn't solve the underlying shared-IP problem, just moves the threshold
- Zone memory increase needed (1m -> 2m) to hold more tracking entries

**Effort:** Low (config change only)
**Risk:** Low

---

### Solution 2: Add Redis-Based Rate Limiting (Recommended)

**What:** Introduce Redis as a centralized rate limit store, replacing nginx's in-memory `limit_req`. Implement rate limiting in the Pyramid application layer using a Redis-backed sliding window or token bucket.

**Architecture:**
```
User -> CloudFlare -> nginx (no rate limiting) -> gunicorn -> Pyramid middleware -> Redis
                                                                    |
                                                                    +-- 429 with context
                                                                    +-- New Relic visibility
                                                                    +-- Custom keys possible
```

**Implementation approach:**

1. **Add Redis to infrastructure**
   - Add `redis` service to `docker-compose.yml`
   - Add `REDIS_URL` to environment config
   - Add `redis` Python package to `requirements/prod.in`

2. **Rate limit middleware or Pyramid tween**
   - Implement a Pyramid tween that checks rate limits before request processing
   - Use Redis `MULTI/EXEC` with sliding window counters (or a library like `limits` or `python-redis-rate-limit`)
   - Return 429 with `Retry-After` header and useful error context

3. **Flexible rate limit keys**
   - Default: IP-based (same as current)
   - Authenticated: token-based (same as current)
   - New: support composite keys (IP + URI, IP + user-agent, etc.)
   - New: support partner-specific overrides (Bio gets higher limits)
   - New: support header-based identification (e.g., `X-Client-Id` for partners)

4. **Per-endpoint configuration**
   ```python
   RATE_LIMITS = {
       "api.badge": {"rate": "30/s", "burst": 200, "key": "ip+uri"},
       "api.search": {"rate": "10/s", "burst": 100, "key": "ip"},
       "api.annotations.create": {"rate": "5/s", "burst": 20, "key": "token_or_ip"},
       "api.bulk": {"rate": "1/s", "burst": 5, "key": "token"},
   }

   PARTNER_OVERRIDES = {
       "bioarchive": {"api.search": {"rate": "100/s", "burst": 500}},
   }
   ```

**Why Redis specifically:**
- Centralized state shared across all gunicorn workers and pods
- Atomic operations (`INCR`, `EXPIRE`, `EVALSHA`) for accurate counting
- Sub-millisecond latency — negligible overhead per request
- Built-in TTL for automatic key expiry (no manual cleanup)
- Proven pattern: virtually every major API uses Redis for rate limiting
- We can also use it for badge response caching (see Solution 4)

**Pros:**
- Full visibility in New Relic (rate limiting happens in Python now)
- Consistent limits across workers/pods (nginx `limit_req` is per-worker memory)
- Flexible keys solve the shared-IP problem (key by IP+URI means same IP requesting different pages gets separate buckets)
- Partner-specific overrides without nginx config changes
- `Retry-After` header tells clients exactly when to retry
- Foundation for future features (API keys, usage tiers, partner dashboards)

**Cons:**
- New infrastructure dependency (Redis)
- More complex than nginx config change
- Redis becomes a critical path dependency (need to decide fail-open or fail-closed)
- Latency: adds one Redis round-trip per request (~0.5ms local, ~1-2ms network)

**Fail-open strategy:** If Redis is unavailable, allow the request through (no rate limiting) rather than blocking all traffic. Log the Redis failure to New Relic for alerting.

**Effort:** Medium (2-3 days implementation + testing)
**Risk:** Medium (new dependency, but well-understood pattern)

---

### Solution 3: CloudFlare Rate Limiting

**What:** Use CloudFlare's built-in rate limiting rules instead of/in addition to nginx.

**How:**
- Configure rate limiting rules in CloudFlare dashboard
- Rules can match on path patterns (`/api/badge*`, `/api/*`)
- Can use different thresholds per rule
- CloudFlare handles the 429 responses at the edge

**Pros:**
- No code changes
- Rate limiting happens at the edge (before traffic even reaches our infrastructure)
- CloudFlare has better IP intelligence (can distinguish real users from bots)
- Built-in analytics dashboard for rate limit events
- Can handle DDoS-scale traffic that would overwhelm nginx

**Cons:**
- Less control over rate limit keys (limited to what CloudFlare exposes)
- CloudFlare rate limiting is a paid feature (Enterprise or specific add-on)
- Harder to do partner-specific overrides
- Rate limit logic lives outside our codebase (not version-controlled)
- Vendor lock-in for a critical traffic control feature
- Still doesn't solve the shared-IP problem (CloudFlare sees the same NAT'd IP)

**Effort:** Low (configuration only)
**Risk:** Low-Medium (depends on CloudFlare plan/features available)

---

### Solution 4: Search/Badge Response Caching (Complementary)

**What:** Cache API responses to reduce the number of requests that actually need rate limiting. This doesn't replace rate limiting but dramatically reduces the load.

**Observation:** Bio calls `/api/search` with versioned URIs (e.g., `uri=https://example.com/article:v1:v2`) to get annotation counts per article version. These counts change infrequently (only when someone creates/deletes an annotation), but every page load queries them fresh. The same is true for badge counts.

**Option A: HTTP Cache Headers on Search (simplest for Bio's case)**

Add short-lived cache headers to search responses when the query is for public/unauthenticated data:

```python
# In search view (h/views/api/annotations.py), for unauthenticated requests:
if not request.authenticated_userid:
    cache_control = request.response.cache_control
    cache_control.prevent_auto = True
    cache_control.public = True
    cache_control.max_age = 60  # 1 minute cache
```

This means CloudFlare and browsers cache the response. 200 users hitting the same search query within 60 seconds = 1 actual backend request.

**Conference scenario with 60s cache:** Instead of 600 requests, effectively 3 requests (one per unique versioned URI query) per minute. Problem eliminated at the HTTP layer.

**Caveat:** Search responses can be large (up to 200 annotations with full JSON). Caching large JSON payloads at the CloudFlare edge uses bandwidth. For count-only use cases, Bio could use `limit=0` to get just the total without annotation bodies — this produces a tiny cacheable response.

**Option A2: HTTP Cache Headers on Badge**

Same approach for `/api/badge` (currently only blocked URIs get cache headers in `badge.py:97-100`):

```python
# In badge view, after computing count:
cache_control = request.response.cache_control
cache_control.prevent_auto = True
cache_control.public = True
cache_control.max_age = 60  # 1 minute cache
```

**Option B: Redis Application Cache (requires Solution 2 infrastructure)**

If we add Redis, cache search totals and badge counts in Redis:

```python
# For search count caching:
cache_key = f"search_total:{normalize(uri)}:{version_suffix}"
cached_total = redis.get(cache_key)
if cached_total is not None:
    # Still need to run the full search for annotation bodies,
    # but can skip it if client only needs the count (limit=0)
    ...

# For badge caching:
cache_key = f"badge:{normalize(uri)}"
cached = redis.get(cache_key)
if cached is not None:
    return {"total": int(cached)}
```

Invalidate on annotation create/delete via the existing Celery task pipeline.

**Pros:**
- Dramatically reduces request volume for the most common queries
- Cache headers work at every layer (browser, CloudFlare, nginx)
- For the conference scenario, this alone solves the problem
- Low staleness risk (annotation counts don't change every second)

**Cons:**
- Stale counts for up to cache TTL (60s is reasonable)
- HTTP caching of search responses may cache stale annotation data (not just counts)
- Option B requires Redis infrastructure
- Cache invalidation adds complexity if we want real-time accuracy

**Effort:** Option A: Very Low (few lines of code). Option B: Low-Medium (requires Redis)
**Risk:** Low

---

### Solution 5: 429 Monitoring and Slack Alerting (Must-Do Regardless)

**What:** Add visibility into rate limiting events, with Slack alerts when limits are being hit.

**This is needed regardless of which rate limiting solution we choose.** We're currently blind.

**Implementation:**

#### Step 1: Enable nginx Access Logging

```nginx
# Add to http block in nginx.conf
log_format json_combined escape=json
  '{'
    '"time_local":"$time_local",'
    '"remote_addr":"$remote_addr",'
    '"cf_connecting_ip":"$http_cf_connecting_ip",'
    '"request":"$request",'
    '"status":$status,'
    '"body_bytes_sent":$body_bytes_sent,'
    '"http_authorization_present":"$http_authorization",'
    '"request_time":$request_time,'
    '"limit_req_status":"$limit_req_status"'
  '}';

# Change from off to:
access_log /dev/stdout json_combined;
```

#### Step 2: Ship Logs to New Relic

If using New Relic Infrastructure agent, configure log forwarding. Alternatively, use Fluent Bit or similar lightweight log shipper.

#### Step 3: New Relic NRQL Alert

```sql
-- Alert: Rate limiting spike
SELECT count(*)
FROM Log
WHERE status = 429
FACET cf_connecting_ip, request
SINCE 5 minutes ago
```

Alert conditions:
- **Warning:** >10 429s per minute (somebody hit a limit)
- **Critical:** >100 429s per minute (widespread rate limiting, likely affecting real users)

#### Step 4: Slack Integration

Route New Relic alerts to a Slack channel (e.g., `#api-alerts` or `#developers`).

**If we go with Redis-based rate limiting (Solution 2):**

Monitoring becomes much simpler because rate limiting happens in Python:

```python
# In the rate limit tween/middleware
import newrelic.agent

if rate_limited:
    newrelic.agent.record_custom_event("RateLimitHit", {
        "endpoint": request.path,
        "key": rate_limit_key,
        "ip": request.client_addr,
        "limit": current_limit,
        "remaining": remaining,
    })
    # Return 429
```

New Relic sees it natively. No log parsing needed.

**Effort:** Medium
**Risk:** Low

---

## Recommendation

### Phase 1: Immediate (this week)
1. **Solution 1:** Bump general API rate limit to `rate=10r/s, burst=100 nodelay` and badge to `rate=10r/s, burst=100 nodelay` — buys immediate headroom for Bio's search API usage and badge consumers
2. **Solution 4A:** Add `Cache-Control: public, max-age=60` to unauthenticated search and badge responses — this alone neutralizes the conference scenario (600 requests -> ~3)
3. **Solution 5 (partial):** Enable nginx access logging with status codes so we at least have logs to grep

### Phase 2: Short-term (next 2-3 weeks)
4. **Solution 2:** Add Redis, implement application-layer rate limiting with flexible keys and partner overrides
5. **Solution 5 (full):** New Relic custom events for rate limit hits + NRQL alert -> Slack notification
6. **Solution 4B:** Redis-backed search/badge caching with invalidation on annotation create/delete

### Phase 3: Evaluate
7. **Solution 3:** Evaluate CloudFlare rate limiting as an additional edge-layer defense (depends on our plan/features)

### Why this order
- Phase 1 is all config/code changes with no new infrastructure — deployable immediately
- Search response caching (4A) is the highest-impact single change: the conference scenario goes from 4,000 requests to ~20 (the unique paginated queries) per minute
- Phase 2 builds the proper foundation (Redis) that enables both smarter rate limiting, caching, and the Slack alerting we need
- Phase 3 is optional defense-in-depth at the edge

### Note on Bio's Versioned URI Queries
Bio uses Karen's versioning feature (#10078/#10093) to query annotations by article version via the search API (e.g., `uri=https://example.com/article:v1`). The `parse_uri_versions()` function in `h/util/uri.py` parses these into base URI + version list, and `UriCombinedWildcardFilter` in `h/search/query.py` builds the appropriate Elasticsearch queries. Each versioned query is a separate search API call. If Bio could consolidate their 3 calls into fewer calls (e.g., using `:all` to match all versions in a single request, or using `_separate_replies=true`), that would reduce their per-user request count at the source.

---

## Appendix: Current Rate Limit Key Behavior

| Request Type | Authorization Header | Rate Limit Key | Implication |
|---|---|---|---|
| Authenticated | `Bearer xxx` | The token value | Each API key gets own bucket |
| Unauthenticated (via CloudFlare) | empty | `CF-Connecting-IP` value | Each real IP gets own bucket |
| Unauthenticated (behind NAT) | empty | Shared NAT IP | All users behind NAT share one bucket |
| Internal service (no CF header) | empty | empty string | **No rate limiting at all** |

Note: When `$limit_per_user` resolves to an empty string, nginx's `limit_req_zone` does not apply rate limiting. This is intentional for internal services but means any request without both an auth header and a CF header bypasses rate limiting entirely.
