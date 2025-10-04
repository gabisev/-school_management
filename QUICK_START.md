# 🚀 Guide de Démarrage Rapide

Ce guide vous permettra de démarrer rapidement avec le système de gestion scolaire.

## ⚡ Installation Express (5 minutes)

### Option 1: Installation Automatique
```bash
# Cloner le dépôt
git clone https://github.com/votre-username/school_management.git
cd school_management

# Configuration automatique
python setup_dev.py
```

### Option 2: Installation Manuelle
```bash
# 1. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configuration
cp env.example .env
# Éditez .env avec vos paramètres

# 4. Base de données
python manage.py migrate

# 5. Superutilisateur
python manage.py createsuperuser

# 6. Lancer le serveur
python manage.py runserver
```

## 🐳 Avec Docker (2 minutes)

```bash
# Développement
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## 🔑 Connexion

- **URL** : http://127.0.0.1:8000
- **Admin** : http://127.0.0.1:8000/admin
- **Utilisateur par défaut** : admin / admin123

## 📋 Premiers Pas

1. **Connectez-vous** avec le compte administrateur
2. **Créez des classes** via l'interface d'administration
3. **Ajoutez des matières** dans la section Matières
4. **Créez des utilisateurs** (élèves, professeurs, parents)
5. **Configurez les emplois du temps**

## 🛠️ Commandes Utiles

```bash
# Tests
make test

# Qualité du code
make lint
make format

# Docker
make docker-up
make docker-down

# Aide complète
make help
```

## 🆘 Problèmes Courants

### Erreur de base de données
```bash
python manage.py migrate
```

### Erreur de permissions
```bash
chmod +x setup_dev.py
chmod +x deploy.sh
```

### Port déjà utilisé
```bash
python manage.py runserver 8001
```

## 📚 Documentation Complète

- [README.md](README.md) - Documentation complète
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guide de contribution
- [Docker](docker-compose.yml) - Configuration Docker

## 🎯 Prochaines Étapes

1. Explorez l'interface d'administration
2. Créez vos premières données de test
3. Configurez les paramètres de production
4. Déployez sur votre serveur

---

**Besoin d'aide ?** Consultez la documentation complète ou créez une issue sur GitHub.
