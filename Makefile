# =============================================================================
# CarbonPilot Edge Cases Testing Makefile
# Automatizza l'intera catena di test per gli edge cases del nesting
# =============================================================================

.PHONY: help edge reset seed test report clean start-backend start-frontend check-services

# Variabili
PYTHON := python
BACKEND_DIR := backend
FRONTEND_DIR := frontend
TOOLS_DIR := tools

# Target di default
help: ## Mostra questo messaggio di aiuto
	@echo "🛠️  CarbonPilot Edge Cases Testing"
	@echo "=================================="
	@echo ""
	@echo "Comandi disponibili:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🚀 Comando principale:"
	@echo "  make edge    # Esegue tutta la catena di test edge cases"
	@echo ""

# =============================================================================
# COMANDO PRINCIPALE
# =============================================================================

edge: ## 🚀 Esegue tutta la catena di test edge cases (reset + seed + test)
	@echo "🚀 AVVIO CATENA COMPLETA EDGE CASES TEST"
	@echo "========================================"
	@echo ""
	@echo "📋 Passaggi:"
	@echo "  1. Reset database"
	@echo "  2. Seed dati edge cases"
	@echo "  3. Esecuzione test scenari"
	@echo "  4. Generazione report"
	@echo ""
	@read -p "⚠️  Questo resetterà il database. Continuare? [y/N] " confirm && [ "$$confirm" = "y" ]
	@echo ""
	$(MAKE) reset
	@echo ""
	$(MAKE) seed
	@echo ""
	$(MAKE) test
	@echo ""
	@echo "🎉 CATENA EDGE CASES COMPLETATA!"
	@echo "📄 Controlla:"
	@echo "   - docs/nesting_edge_report.md (report dettagliato)"
	@echo "   - logs/nesting_edge_tests.log (log completo)"

# =============================================================================
# SINGOLI PASSI
# =============================================================================

reset: ## 📥 Reset del database (alembic downgrade base + upgrade head)
	@echo "📥 RESET DATABASE"
	@echo "=================="
	@echo ""
	@cd $(TOOLS_DIR) && $(PYTHON) reset_db.py

seed: ## 🌱 Carica dati edge cases nel database
	@echo "🌱 SEED EDGE CASES DATA"
	@echo "======================="
	@echo ""
	@cd $(TOOLS_DIR) && $(PYTHON) seed_edge_data.py

test: ## 🧪 Esegue tutti i test degli edge cases
	@echo "🧪 ESECUZIONE TEST EDGE CASES"
	@echo "============================="
	@echo ""
	@cd $(TOOLS_DIR) && $(PYTHON) edge_tests.py

report: ## 📄 Genera solo il report (richiede test già eseguiti)
	@echo "📄 Ultimi report generati:"
	@echo ""
	@ls -la docs/nesting_edge_report.md 2>/dev/null || echo "   Nessun report trovato"
	@echo ""
	@ls -la logs/nesting_edge_tests*.json 2>/dev/null | tail -3 || echo "   Nessun log JSON trovato"

# =============================================================================
# SERVIZI DI SUPPORTO
# =============================================================================

start-backend: ## 🔧 Avvia il backend FastAPI
	@echo "🔧 AVVIO BACKEND"
	@echo "================"
	@echo ""
	@echo "📍 Avvio backend su http://localhost:8000"
	@cd $(BACKEND_DIR) && uvicorn main:app --reload --port 8000

start-frontend: ## 🎨 Avvia il frontend NextJS
	@echo "🎨 AVVIO FRONTEND"
	@echo "================="
	@echo ""
	@echo "📍 Avvio frontend su http://localhost:3000"
	@cd $(FRONTEND_DIR) && npm run dev

build-frontend: ## 🏗️  Build del frontend per produzione
	@echo "🏗️  BUILD FRONTEND"
	@echo "=================="
	@echo ""
	@cd $(FRONTEND_DIR) && npm run build

start-frontend-prod: build-frontend ## 🚀 Avvia frontend in modalità produzione
	@echo "🚀 AVVIO FRONTEND PRODUZIONE"
	@echo "============================"
	@echo ""
	@cd $(FRONTEND_DIR) && npm run start

check-services: ## 🔍 Verifica che backend e frontend siano attivi
	@echo "🔍 VERIFICA SERVIZI"
	@echo "==================="
	@echo ""
	@echo "🔧 Backend (http://localhost:8000):"
	@curl -s http://localhost:8000/docs >/dev/null && echo "   ✅ Backend attivo" || echo "   ❌ Backend non raggiungibile"
	@echo ""
	@echo "🎨 Frontend (http://localhost:3000):"
	@curl -s http://localhost:3000 >/dev/null && echo "   ✅ Frontend attivo" || echo "   ❌ Frontend non raggiungibile"

# =============================================================================
# UTILITÀ
# =============================================================================

clean: ## 🧹 Pulisce file temporanei e cache
	@echo "🧹 PULIZIA FILE TEMPORANEI"
	@echo "=========================="
	@echo ""
	@echo "🗑️  Rimozione cache Python..."
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "🗑️  Rimozione file di build frontend..."
	@rm -rf $(FRONTEND_DIR)/.next 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/node_modules/.cache 2>/dev/null || true
	@echo "✅ Pulizia completata"

install-deps: ## 📦 Installa dipendenze Python e Node.js
	@echo "📦 INSTALLAZIONE DIPENDENZE"
	@echo "============================"
	@echo ""
	@echo "🐍 Installazione dipendenze Python..."
	@cd $(BACKEND_DIR) && pip install -r requirements.txt
	@echo ""
	@echo "📊 Installazione dipendenze Node.js..."
	@cd $(FRONTEND_DIR) && npm install
	@echo "✅ Installazione completata"

show-logs: ## 📜 Mostra gli ultimi log dei test
	@echo "📜 ULTIMI LOG TEST EDGE CASES"
	@echo "============================="
	@echo ""
	@if [ -f "logs/nesting_edge_tests.log" ]; then \
		echo "📝 Contenuto logs/nesting_edge_tests.log:"; \
		echo ""; \
		tail -50 logs/nesting_edge_tests.log; \
	else \
		echo "❌ File log non trovato. Esegui prima 'make test'"; \
	fi

show-report: ## 📄 Mostra l'ultimo report generato
	@echo "📄 ULTIMO REPORT EDGE CASES"
	@echo "==========================="
	@echo ""
	@if [ -f "docs/nesting_edge_report.md" ]; then \
		cat docs/nesting_edge_report.md; \
	else \
		echo "❌ Report non trovato. Esegui prima 'make test'"; \
	fi

# =============================================================================
# TEST MANUALI
# =============================================================================

manual-test: ## 🖱️  Guida per test manuale finale
	@echo "🖱️  TEST MANUALE FINALE"
	@echo "======================"
	@echo ""
	@echo "📋 Passi per test manuale:"
	@echo ""
	@echo "1. 🔧 Avvia backend:"
	@echo "   uvicorn backend.main:app --port 8000 &"
	@echo ""
	@echo "2. 🎨 Avvia frontend:"
	@echo "   cd frontend && npm run start &"
	@echo ""
	@echo "3. 🌐 Apri browser:"
	@echo "   http://localhost:3000/nesting"
	@echo ""
	@echo "4. ✅ Verifica:"
	@echo "   - Pagina carica senza errori"
	@echo "   - Canvas nesting è visibile"
	@echo "   - Console browser senza errori JavaScript"
	@echo ""
	@echo "💡 Usa 'make check-services' per verificare che i servizi siano attivi"

# =============================================================================
# GIT E VERSIONING
# =============================================================================

commit-tag: ## 🏷️  Commit e tag per v1.4.13-DEMO
	@echo "🏷️  COMMIT E TAG v1.4.13-DEMO"
	@echo "============================="
	@echo ""
	@echo "📋 File da committare:"
	@git status --porcelain | grep -E "(docs/|logs/|tools/|Makefile)" || echo "   Nessun file modificato"
	@echo ""
	@read -p "💾 Continuare con commit e tag? [y/N] " confirm && [ "$$confirm" = "y" ]
	@git add docs/ logs/ tools/ Makefile
	@git commit -m "test: edge scenarios + report nesting"
	@git tag v1.4.13-DEMO
	@echo "✅ Commit e tag creati"
	@echo "📤 Per pushare: git push origin main && git push origin v1.4.13-DEMO"

# =============================================================================
# INFORMAZIONI E DEBUG
# =============================================================================

info: ## ℹ️  Mostra informazioni sul sistema
	@echo "ℹ️  INFORMAZIONI SISTEMA"
	@echo "======================="
	@echo ""
	@echo "🐍 Python:"
	@$(PYTHON) --version
	@echo ""
	@echo "📊 Node.js:"
	@node --version 2>/dev/null || echo "   Node.js non installato"
	@echo ""
	@echo "📦 NPM:"
	@npm --version 2>/dev/null || echo "   NPM non installato"
	@echo ""
	@echo "📂 Directory di lavoro:"
	@pwd
	@echo ""
	@echo "🗂️  Struttura file:"
	@ls -la | head -10

debug: ## 🐛 Informazioni di debug per troubleshooting
	@echo "🐛 DEBUG INFORMAZIONI"
	@echo "===================="
	@echo ""
	@echo "📋 Verifica file essenziali:"
	@ls -la $(TOOLS_DIR)/reset_db.py 2>/dev/null && echo "   ✅ reset_db.py" || echo "   ❌ reset_db.py mancante"
	@ls -la $(TOOLS_DIR)/seed_edge_data.py 2>/dev/null && echo "   ✅ seed_edge_data.py" || echo "   ❌ seed_edge_data.py mancante"
	@ls -la $(TOOLS_DIR)/edge_tests.py 2>/dev/null && echo "   ✅ edge_tests.py" || echo "   ❌ edge_tests.py mancante"
	@echo ""
	@echo "🗂️  Database:"
	@ls -la $(BACKEND_DIR)/carbonpilot.db 2>/dev/null && echo "   ✅ Database presente" || echo "   ❌ Database mancante"
	@echo ""
	@echo "📊 Alembic:"
	@ls -la $(BACKEND_DIR)/alembic.ini 2>/dev/null && echo "   ✅ alembic.ini presente" || echo "   ❌ alembic.ini mancante" 