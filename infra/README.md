# Infrastructure

Infrastructure-as-code and deployment assets for rescue-net.eu
(manual §11, §17, §18).

```
infra/
  docker/      docker-compose stack for local/reference deployment
  terraform/   cloud infrastructure (Hetzner Cloud EU, DNS, etc.)
  ansible/     optional node bootstrap and hardening (manual §18.4)
```

## Quick start (local stack)

```bash
docker compose -f infra/docker/docker-compose.yml up --build
# API:  http://localhost:8000/healthz
# Web:  http://localhost:3000
```

`terraform/` and `ansible/` are placeholders to be filled in during the
deployment-automation phase (manual §27, step 16).
