# HPP AI Agent Suite — common tasks. `make help` lists targets.
.PHONY: help install test demo evals eval-denial lint-cfn decks roi clean
AGENT ?= 01-revenue-cycle-denial

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n",$$1,$$2}'

install: ## Install platform_core (editable) + agent deps
	pip install -e platform_core && pip install langgraph streamlit

test: ## Run the full test suite (no API key), per-agent isolation
	bash scripts/run_tests.sh

demo: ## Run a deterministic agent demo (AGENT=0N-name), no API key
	cd $(AGENT)-agent && EXTRACT_MODE=demo python demo/demo_run.py

evals: ## Run the governance structural eval harness
	PYTHONPATH=platform_core:. python -m governance.evals.run_evals

eval-denial: ## Run the scored denial benchmark (Agent 01) — gates on thresholds
	PYTHONPATH=platform_core:. python -m governance.evals.score_denial

lint-cfn: ## cfn-lint all CloudFormation templates
	cfn-lint infra/cloudformation/*.yaml

decks: ## Regenerate the GTM decks (requires pptxgenjs)
	cd decks && node build-agent-decks.js

roi: ## Regenerate the ROI calculator workbook
	cd gtm/roi-calculator && python build_roi_calculator.py

clean: ## Remove caches
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null; rm -rf .pytest_cache
