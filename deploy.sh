#!/bin/bash

# Script de déploiement pour School Management System
# Usage: ./deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
echo "🚀 Déploiement en mode: $ENVIRONMENT"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    log_error "manage.py non trouvé. Assurez-vous d'être dans le répertoire du projet."
    exit 1
fi

# Vérifier que l'environnement virtuel est activé
if [ -z "$VIRTUAL_ENV" ]; then
    log_warn "Environnement virtuel non détecté. Activation recommandée."
fi

# Installer/mettre à jour les dépendances
log_info "Installation des dépendances..."
pip install -r requirements.txt

if [ "$ENVIRONMENT" = "production" ]; then
    pip install -r requirements-dev.txt
fi

# Exécuter les migrations
log_info "Exécution des migrations..."
python manage.py makemigrations
python manage.py migrate

# Collecter les fichiers statiques
log_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer le répertoire de logs s'il n'existe pas
mkdir -p logs

# Vérifier la configuration
log_info "Vérification de la configuration..."
python manage.py check --deploy

# Redémarrer les services (à adapter selon votre configuration)
if [ "$ENVIRONMENT" = "production" ]; then
    log_info "Redémarrage des services..."
    # Exemples de commandes (à adapter selon votre setup)
    # sudo systemctl restart gunicorn
    # sudo systemctl restart nginx
    # sudo systemctl restart postgresql
fi

# Tests de santé
log_info "Tests de santé..."
python manage.py check

log_info "✅ Déploiement terminé avec succès!"

# Afficher les informations utiles
echo ""
echo "📋 Informations utiles:"
echo "- URL: http://localhost:8000"
echo "- Admin: http://localhost:8000/admin"
echo "- Logs: tail -f logs/django.log"
echo "- Status: python manage.py runserver"
