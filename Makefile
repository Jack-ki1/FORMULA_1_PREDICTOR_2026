.PHONY: install setup predict test quality serve dashboard clean

install:
	pip install -r requirements.txt

setup: install
	py main.py migrate-db

predict:
	py main.py predict --race canada --sims 5000

test:
	pytest tests/ -v --tb=short

quality:
	py main.py quality-check

serve:
	py main.py api --port 8000

dashboard:
	py main.py dashboard --port 5000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
