# Deploying to AWS (single VM) + Cloudflare

Target: one Lightsail VM running Docker Compose (Postgres + API + ingest loop + Caddy),
with Cloudflare in front for DNS, TLS, and caching. ~$10/month.

## 0. Prerequisites (one-time)

- Buy your domain on Cloudflare Registrar (Cloudflare dashboard -> Domain Registration).
- Put this repo on GitHub (private is fine):
  ```powershell
  cd C:\Users\willi\projects\fairfield-events
  git init
  git add .
  git commit -m "initial"
  # create a repo on github.com, then:
  git remote add origin https://github.com/YOURUSER/fairfield-events.git
  git push -u origin main
  ```

## 1. Create the server (AWS Lightsail)

1. AWS Console -> Lightsail -> Create instance.
2. Region: us-east-1 (closest to CT). Platform: Linux, blueprint: **Ubuntu 24.04 LTS** (OS only).
3. Plan: **$10/mo (2 GB RAM)** — 1 GB struggles to build the frontend image.
4. Name it `fairfield-events`, create.
5. Networking tab -> Create **static IP** and attach it. Note the IP.
6. Networking tab -> Firewall: ensure rules for **SSH (22), HTTP (80), HTTPS (443)**.

## 2. Install Docker on the server

Connect via the browser SSH button (or `ssh ubuntu@STATIC_IP` with the downloaded key), then:

```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu && exit   # log out/in so group applies
```

## 3. Deploy the app

```bash
git clone https://github.com/YOURUSER/fairfield-events.git
cd fairfield-events/deploy
cp .env.example .env
nano .env        # set DOMAIN, ADMIN_PASSWORD, POSTGRES_PASSWORD
docker compose up -d --build
docker compose logs -f ingest   # watch the first ingestion run; Ctrl+C to stop watching
```

Check: `curl -s localhost/healthz` on the server should return `{"ok":true}`.

## 4. Point Cloudflare at it

1. Cloudflare dashboard -> your domain -> DNS -> Add record:
   - Type **A**, name `events` (or `@` for the bare domain), IPv4 = your static IP,
     Proxy status: **Proxied** (orange cloud).
2. SSL/TLS -> Overview -> set mode to **Full** (not Flexible, not Full-strict yet).
   Caddy will obtain its own Let's Encrypt certificate automatically on first request.
3. Visit https://events.yourdomain.com — calendar should load.
4. Optional hardening: SSL/TLS -> Edge Certificates -> enable "Always Use HTTPS".

## 5. Operations

| Task | Command (in `~/fairfield-events/deploy`) |
|---|---|
| Deploy an update | `git pull && docker compose up -d --build` |
| Tail API logs | `docker compose logs -f api` |
| Tail ingest logs | `docker compose logs -f ingest` |
| Run ingest now | `docker compose exec ingest python -m ingest.runner` |
| DB shell | `docker compose exec db psql -U events events` |
| Backup DB | `docker compose exec db pg_dump -U events events > backup_$(date +%F).sql` |

Nightly DB backup (optional): `crontab -e` and add
```
0 3 * * * cd ~/fairfield-events/deploy && docker compose exec -T db pg_dump -U events events | gzip > ~/backups/events_$(date +\%F).sql.gz
```
(`mkdir -p ~/backups` first.)

## Notes / gotchas

- **Moderation** lives at `https://YOUR_DOMAIN/admin` with ADMIN_PASSWORD from `.env`.
- The API runs a **single worker** on purpose — the submission rate limiter is
  in-process. Don't add `--workers N` without moving the limiter to Redis/Postgres.
- Event data is re-fetchable from feeds; user submissions are the only
  irreplaceable data — that's what the DB backup protects.
- `/docs` (interactive API docs) is publicly reachable; harmless, but you can
  remove its block in `deploy/Caddyfile` if you'd rather hide it.
- Norwalk's town site blocks datacenter IPs — that may include AWS, so the
  Norwalk town feed (when added) might only work via a different source. Test
  from the server with: `docker compose exec ingest python -m ingest.verify_sources`.
