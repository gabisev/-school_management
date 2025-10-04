# Makefile pour School Management System

.PHONY: help install test lint format clean run docker-build docker-up docker-down

# Variables
PYTHON = python
PIP = pip
MANAGE = python manage.py

# Aide
help: ## Affiche cette aide
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Installe les dépendances
	$(PIP) install -r requirements.txt

install-dev: ## Installe les dépendances de développement
	$(PIP) install -r requirements-dev.txt

# Base de données
migrate: ## Exécute les migrations
	$(MANAGE) makemigrations
	$(MANAGE) migrate

# Tests
test: ## Lance les tests
	$(MANAGE) test

test-pytest: ## Lance les tests avec pytest
	pytest

test-coverage: ## Lance les tests avec couverture
	pytest --cov=school_management --cov-report=html

# Qualité du code
lint: ## Vérifie la qualité du code
	flake8 .
	black --check .
	isort --check-only .
	mypy .

format: ## Formate le code
	black .
	isort .

# Serveur
run: ## Lance le serveur de développement
	$(MANAGE) runserver

run-prod: ## Lance le serveur de production
	gunicorn school_system.wsgi:application --config gunicorn.conf.py

# Docker
docker-build: ## Construit l'image Docker
	docker build -t school-management .

docker-up: ## Lance les conteneurs Docker
	docker-compose up -d

docker-down: ## Arrête les conteneurs Docker
	docker-compose down

docker-logs: ## Affiche les logs Docker
	docker-compose logs -f

# Développement
setup: ## Configure l'environnement de développement
	$(PYTHON) setup_dev.py

clean: ## Nettoie les fichiers temporaires
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Déploiement
deploy: ## Déploie l'application
	./deploy.sh

# Collecte des fichiers statiques
collectstatic: ## Collecte les fichiers statiques
	$(MANAGE) collectstatic --noinput

# Création d'un superutilisateur
createsuperuser: ## Crée un superutilisateur
	$(MANAGE) createsuperuser

# Vérification
check: ## Vérifie la configuration
	$(MANAGE) check

check-deploy: ## Vérifie la configuration de déploiement
	$(MANAGE) check --deploy

# Shell Django
shell: ## Ouvre le shell Django
	$(MANAGE) shell

# Base de données
dbshell: ## Ouvre le shell de la base de données
	$(MANAGE) dbshell

# Logs
logs: ## Affiche les logs
	tail -f logs/django.log

# Sécurité
security: ## Vérifie la sécurité
	safety check
	bandit -r .

# Documentation
docs: ## Génère la documentation
	sphinx-build -b html docs/ docs/_build/

# Environnements Docker
dev: ## Lance l'environnement de développement
	docker-compose -f docker-compose.dev.yml up -d

staging: ## Lance l'environnement de staging
	docker-compose -f docker-compose.staging.yml up -d

prod: ## Lance l'environnement de production
	docker-compose -f docker-compose.prod.yml up -d

# Tests Docker
test-docker: ## Lance les tests dans Docker
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Nettoyage Docker
docker-clean: ## Nettoie les images et conteneurs Docker
	docker system prune -f
	docker volume prune -f