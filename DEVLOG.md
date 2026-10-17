# Devlog

Append-only. Newest entry at the bottom. One entry per working session:
what changed, what was measured, what broke, what is next. Write down the
things that cost time — the trap you hit is worth more to the next session
than the feature you shipped.

---

## 2026-10-18 — infrastructure and project setup

**Server.** Oracle Cloud Always Free, Ampere A1, 4 OCPU / 24 GB, Mumbai
(`ap-mumbai-1`, single AD). Reserved IP `152.67.31.231`. The instance took
11 retries over ~45 minutes to land — `Out of host capacity` is the normal
state in Mumbai, and a retry loop is the answer. `~/oci/retry-launch.sh` on
the dev machine still works if the box ever needs rebuilding.

Installed: PostgreSQL 16.15 (tuned: `shared_buffers 6GB`,
`effective_cache_size 18GB`, `random_page_cost 1.1`, localhost only),
Redis 7.0.15, Caddy 2.11.7, Python 3.12.3, fail2ban, unattended-upgrades.

*Trap:* Oracle's Ubuntu images block 80/443 in iptables even when the VCN
security list allows them. Had to insert ACCEPT rules above the catch-all
REJECT and persist them. Cloud-side rules alone do nothing.

*Trap:* adding `log { output file /var/log/caddy/… }` to the Caddyfile makes
Caddy fail to reload with "permission denied" — the packaged unit sets
`ProtectSystem=full`, so `/var` is read-only no matter who owns the
directory. Logs go to journald.

**HTTPS.** https://study.hawayu.in live with a Let's Encrypt certificate,
HTTP 308s to HTTPS. Apex and `www` still point at Vercel and were left alone.

*Trap:* the DNS record appeared to be "propagating" for an hour. It had never
been saved — the zone serial at the authoritative nameserver was still three
days old. Querying the authoritative server directly settles this in seconds;
a cached resolver cannot tell you the difference between slow and absent.

**Schema v3 reviewed, fixed and tested.** Two different copies existed — a
472-line one and a 624-line one inside the design zip. The zip is
authoritative. Nine defects found, all tagged `[R-n]` in
`../mpsc-question-bankv2/db/mpsc_schema_v3.sql`. The two that mattered:

- `v_scorable` admitted all 40,675 model-inferred answers into mocks and
  duels, contradicting the project's own extraction guide.
- Section 14 quoted every function body with a bare `$` instead of `$$`, so
  the entire moderation block failed with a syntax error and none of its
  seven tables were created. Verified by running it.

**Measured on the real bank** (77,751 questions, not synthetic):

| | |
|---|---|
| COPY whole bank in | 3.8 s |
| v3 migration incl. backfill | 29 s |
| DB size after migration | 282 MB |
| point lookup / 20 scorable / FTS | 0.81 / 0.11 / 0.07–0.51 ms |
| 50 concurrent quiz clients | **5,379 tps**, 9.3 ms latency |
| bulk insert 50,000 attempts | 1.1 s |

Conclusion: performance is not a constraint for this workload. The earlier
worry about free-tier disk I/O throttling writes was wrong. The only slow
things are `ORDER BY random()` (19.8 ms, avoidable) and trigram similarity
(244 ms, batch-only).

**Project set up.** `india-study-map-app` with `web/` and `api/`. Milestone 1
is a vertical slice: Bank → Question detail, deployed.

*Next:* FastAPI service against the `bench` database.
