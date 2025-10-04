# Système de Gestion Scolaire

Un système de gestion scolaire complet développé avec Django, permettant la gestion des élèves, professeurs, parents, matières, notes, bulletins et communications.

## 🚀 Fonctionnalités

### 👥 Gestion des Utilisateurs
- **Élèves** : Gestion des profils, classes, notes et bulletins
- **Professeurs** : Gestion des matières, saisie des notes, bulletins
- **Parents** : Consultation des notes et bulletins de leurs enfants
- **Administrateurs** : Gestion complète du système

### 📚 Gestion Académique
- Gestion des matières et classes
- Saisie et gestion des notes
- Génération automatique des bulletins
- Système d'évaluations et trimestres
- Gestion des absences

### 📅 Planning et Organisation
- Emploi du temps des classes
- Réservation des salles
- Gestion des événements du calendrier
- Planning des professeurs

### 💬 Communication
- Système de messagerie intégré
- Communications entre professeurs, élèves et parents
- Notifications et alertes

### 📊 Rapports et Statistiques
- Tableaux de bord personnalisés par type d'utilisateur
- Statistiques détaillées
- Rapports d'audit et logs

## 🛠️ Technologies Utilisées

- **Backend** : Django 4.2.5
- **Frontend** : HTML, CSS, JavaScript, Bootstrap 4
- **Base de données** : SQLite (développement), PostgreSQL/MySQL (production)
- **Authentification** : Django Auth avec backends personnalisés
- **Interface** : Django Crispy Forms avec Bootstrap 4

## 📋 Prérequis

- Python 3.8+
- pip
- Git

## 🚀 Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/votre-username/school_management.git
cd school_management
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration de l'environnement
```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer le fichier .env avec vos paramètres
# Modifier au minimum SECRET_KEY et DEBUG
```

### 5. Migrations de la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 7. Collecter les fichiers statiques
```bash
python manage.py collectstatic
```

### 8. Lancer le serveur de développement
```bash
python manage.py runserver
```

Le site sera accessible à l'adresse : http://127.0.0.1:8000/

## 🐳 Déploiement avec Docker

### Docker Compose
```bash
# Construire et lancer les conteneurs
docker-compose up --build

# En arrière-plan
docker-compose up -d --build
```

### Docker seul
```bash
# Construire l'image
docker build -t school-management .

# Lancer le conteneur
docker run -p 8000:8000 school-management
```

## 📁 Structure du Projet

```
school_management/
├── school_management/          # Application principale
│   ├── models.py              # Modèles de données
│   ├── views.py               # Vues principales
│   ├── urls.py                # Configuration des URLs
│   ├── forms.py               # Formulaires
│   ├── admin.py               # Interface d'administration
│   ├── management/            # Commandes personnalisées
│   └── migrations/            # Migrations de base de données
├── school_system/             # Configuration du projet
│   ├── settings.py            # Paramètres Django
│   ├── urls.py                # URLs principales
│   └── wsgi.py                # Configuration WSGI
├── templates/                 # Templates HTML
├── static/                    # Fichiers statiques
├── media/                     # Fichiers média
├── requirements.txt           # Dépendances Python
├── requirements-dev.txt       # Dépendances de développement
├── Dockerfile                 # Configuration Docker
├── docker-compose.yml         # Configuration Docker Compose
└── README.md                  # Ce fichier
```

## 🔧 Configuration

### Variables d'environnement importantes

- `SECRET_KEY` : Clé secrète Django (obligatoire)
- `DEBUG` : Mode debug (True pour développement)
- `ALLOWED_HOSTS` : Hôtes autorisés
- `DATABASE_URL` : URL de la base de données
- `EMAIL_*` : Configuration email (optionnel)

### Base de données

Le projet utilise SQLite par défaut pour le développement. Pour la production, configurez PostgreSQL ou MySQL :

```python
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/school_management

# MySQL
DATABASE_URL=mysql://user:password@localhost:3306/school_management
```

## 🧪 Tests

```bash
# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Lancer les tests
python manage.py test

# Avec pytest
pytest

# Avec couverture de code
pytest --cov=school_management
```

## 🔍 Qualité du Code

```bash
# Formater le code
black .

# Vérifier la qualité
flake8

# Trier les imports
isort .

# Vérification des types
mypy .
```

## 📚 Utilisation

### Connexion
1. Accédez à http://127.0.0.1:8000/
2. Connectez-vous avec votre compte administrateur
3. Créez les utilisateurs (élèves, professeurs, parents) via l'interface d'administration

### Gestion des données
- **Élèves** : Création et gestion des profils d'élèves
- **Classes** : Organisation des élèves par classe
- **Matières** : Définition des matières enseignées
- **Notes** : Saisie des notes par les professeurs
- **Bulletins** : Génération automatique des bulletins

## 🤝 Contribution

1. Fork le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation Django
- Vérifiez les logs dans `logs/`

## 🚀 Déploiement en Production

### Checklist de déploiement
- [ ] Changer `SECRET_KEY`
- [ ] Mettre `DEBUG=False`
- [ ] Configurer `ALLOWED_HOSTS`
- [ ] Utiliser une base de données de production
- [ ] Configurer les fichiers statiques
- [ ] Configurer HTTPS
- [ ] Configurer les logs
- [ ] Tester les fonctionnalités critiques

### Serveurs recommandés
- **Nginx** + **Gunicorn** + **PostgreSQL**
- **Apache** + **mod_wsgi** + **MySQL**
- **Docker** + **Docker Compose**

## 📈 Roadmap

- [ ] API REST avec Django REST Framework
- [ ] Application mobile
- [ ] Intégration avec des systèmes externes
- [ ] Notifications push
- [ ] Système de paiement des frais scolaires
- [ ] Module de bibliothèque
- [ ] Gestion des transports scolaires

---

Développé avec ❤️ en Django
