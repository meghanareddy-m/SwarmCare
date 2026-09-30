.PHONY: test coverage benchmark run dashboard scaling reserve
test:
	python -m pytest
coverage:
	python -m pytest --cov=agents --cov=algorithms --cov=evaluation --cov=simulation --cov=experiments --cov=main --cov-report=term-missing
benchmark:
	python main.py --all --pso-seeds 5 --output results --plots --dashboard --quiet
dashboard:
	python -m experiments.dashboard --all --output results/dashboard.html
scaling:
	python -m experiments.scaling --output results --pso-seeds 3
reserve:
	python -m experiments.reserve_policy --output results
run:
	python main.py
