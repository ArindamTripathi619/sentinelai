VENV  := ./venv/bin/python
PIP   := ./venv/bin/pip
BACKEND_PORT := 9000
FRONTEND_PORT := 3000
DC    := docker compose -f docker-compose.monitoring.yml

.PHONY: help install install-backend install-frontend \
        start-backend start-frontend start-monitoring stop-monitoring mon-logs \
        seed-users seed-demo seed-all \
        test test-rules test-scorer test-alignment \
        attack-botwave attack-geodrift attack-speedbot attack-all \
        simulate-varied simulate-load simulate-comprehensive simulate-hackathon \
        train-model model-predict \
        status clean env-check

help:
	@echo "SentinelAI — Development Makefile"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start:  make install && make start-monitoring"
	@echo "Then run backend and frontend in separate terminals."

# ── Install ──────────────────────────────────────────────────────────────────

install: venv-deps frontend-deps ## Install all dependencies (backend + frontend)

install-backend: venv-deps       ## Install only backend Python deps

install-frontend: frontend-deps   ## Install only frontend npm deps

venv-deps: requirements.txt
	$(PIP) install -r requirements.txt

frontend-deps: frontend/package.json
	@cd frontend && npm install

# ── Services ─────────────────────────────────────────────────────────────────

start-backend: env-check          ## Start FastAPI backend (port $(BACKEND_PORT))
	cd backend && ../venv/bin/uvicorn main:app --reload --port $(BACKEND_PORT)

start-frontend:                   ## Start Vite frontend (port $(FRONTEND_PORT))
	@cd frontend && npm run dev

start-monitoring:                 ## Start monitoring stack (Postgres+Prometheus+Grafana)
	$(DC) up -d
	@echo "Postgres :5432  Prometheus :9090  Grafana :3001 (admin/admin)"

stop-monitoring:                  ## Stop monitoring stack
	$(DC) down

mon-logs:                         ## Tail monitoring stack logs
	$(DC) logs -f

# ── Seed Data ────────────────────────────────────────────────────────────────

seed-users: env-check             ## Seed 50 normal users (needs backend running)
	$(VENV) scripts/seed_normal_users.py

seed-demo: env-check              ## Seed demo dashboard (12 users across trust spectrum)
	$(VENV) scripts/seed_demo_dashboard.py

seed-all: seed-users seed-demo    ## Seed all demo data

# ── Tests ────────────────────────────────────────────────────────────────────

test: env-check                   ## Run full offline test suite (from repo root)
	$(VENV) tests/project_suite.py

test-rules:                       ## Run rules engine unit tests (offline, standalone)
	@cd backend && ../venv/bin/python test_rules.py

test-scorer:                      ## Run trust score pipeline tests (offline, standalone)
	@cd backend && ../venv/bin/python test_scorer.py

test-alignment: env-check         ## Run alignment fix integration tests (needs backend)
	@cd backend && ../venv/bin/python test_alignment_fixes.py

# ── Attack Simulations ───────────────────────────────────────────────────────

attack-botwave: env-check         ## Simulate bot wave: 15 regs from single IP
	$(VENV) scripts/simulate_attack.py --scenario botwave

attack-geodrift: env-check        ## Simulate geo drift: cross-country login in <2h
	$(VENV) scripts/simulate_attack.py --scenario geodrift

attack-speedbot: env-check        ## Simulate speed bot: sub-4s registrations
	$(VENV) scripts/simulate_attack.py --scenario speedbot

attack-all: env-check             ## Run all 3 attack scenarios (botwave+geodrift+speedbot)
	$(VENV) scripts/simulate_attack.py --scenario all

simulate-varied: env-check        ## Run varied simulation: bot wave + mixed + stuffing + geo + errors
	$(VENV) scripts/varied_simulation.py

simulate-load: env-check          ## Run load test: 50 users, 10 workers
	$(VENV) scripts/load_test.py --sample-size 50 --workers 10

simulate-comprehensive: env-check ## Run 6 security attack scenarios
	$(VENV) scripts/comprehensive_security_test.py --all

simulate-hackathon: env-check     ## Run hackathon demo (parallel attacks)
	$(VENV) scripts/hackathon_demo.py

# ── ML Model ─────────────────────────────────────────────────────────────────

train-model: env-check            ## Generate training data and retrain Isolation Forest model
	$(VENV) scripts/generate_training_data.py
	cd backend && ../venv/bin/python ml_model.py --train
	@echo "Model saved to backend/ml_model.pkl"

model-predict:                    ## Quick ML sanity check (offline)
	@cd backend && ../venv/bin/python -c "\
	from ml_model import load_model, predict, build_feature_vector; \
	m = load_model(); \
	b = build_feature_vector(180,45,62,1,0.95,88,3); \
	print(f'Benign anomaly: {predict(b, m):.3f}'); \
	a = build_feature_vector(2,1.1,0,14,0.1,44,85); \
	print(f'Bot anomaly:    {predict(a, m):.3f}'); \
	print('OK') if predict(a,m) < predict(b,m) else print('MODEL BROKEN')"

# ── Status & Utility ─────────────────────────────────────────────────────────

status: env-check                 ## Print system status (DB counts, detection coverage)
	$(VENV) scripts/final_status.py

env-check:                        ## Verify .env exists
	@test -f .env || { echo "ERROR: .env not found. Copy .env.example to .env"; exit 1; }
	@echo ".env found"

clean:                            ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned"
