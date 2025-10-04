#!/bin/bash

# Attendre que la base de données soit prête
echo "En attente de la base de données..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Base de données disponible!"

# Exécuter les migrations
echo "Exécution des migrations..."
python manage.py makemigrations
python manage.py migrate

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer un superutilisateur si nécessaire
echo "Création du superutilisateur..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
EOF

# Démarrer le serveur
echo "Démarrage du serveur..."
exec "$@"
