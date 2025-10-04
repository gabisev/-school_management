# Guide de Contribution

Merci de votre intérêt à contribuer au projet School Management System ! Ce document fournit des directives pour contribuer au projet.

## 🚀 Comment Contribuer

### 1. Fork et Clone
1. Fork le dépôt sur GitHub
2. Clone votre fork localement :
   ```bash
   git clone https://github.com/votre-username/school_management.git
   cd school_management
   ```

### 2. Configuration de l'Environnement
1. Créez un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Configurez l'environnement :
   ```bash
   cp env.example .env
   # Éditez .env avec vos paramètres
   ```

4. Exécutez les migrations :
   ```bash
   python manage.py migrate
   ```

### 3. Créer une Branche
```bash
git checkout -b feature/nom-de-votre-fonctionnalite
```

### 4. Développement
- Écrivez du code propre et bien documenté
- Suivez les conventions de style Python (PEP 8)
- Ajoutez des tests pour vos nouvelles fonctionnalités
- Mettez à jour la documentation si nécessaire

### 5. Tests
```bash
# Tests unitaires
python manage.py test

# Tests avec pytest
pytest

# Vérification de la qualité du code
flake8 .
black --check .
isort --check-only .
mypy .
```

### 6. Commit et Push
```bash
git add .
git commit -m "feat: ajouter nouvelle fonctionnalité"
git push origin feature/nom-de-votre-fonctionnalite
```

### 7. Pull Request
1. Créez une Pull Request sur GitHub
2. Décrivez clairement vos changements
3. Référencez les issues liées si applicable

## 📝 Standards de Code

### Style de Code
- Utilisez `black` pour le formatage automatique
- Utilisez `isort` pour trier les imports
- Suivez PEP 8 pour le style Python
- Utilisez des noms de variables et fonctions descriptifs

### Messages de Commit
Utilisez le format conventional commits :
- `feat:` nouvelle fonctionnalité
- `fix:` correction de bug
- `docs:` documentation
- `style:` formatage, point-virgules manquants, etc.
- `refactor:` refactoring du code
- `test:` ajout de tests
- `chore:` maintenance

### Tests
- Écrivez des tests unitaires pour toutes les nouvelles fonctionnalités
- Maintenez une couverture de code élevée
- Testez les cas d'erreur et les cas limites

## 🐛 Signaler un Bug

1. Vérifiez que le bug n'a pas déjà été signalé
2. Créez une issue avec le template de bug
3. Incluez :
   - Description détaillée du problème
   - Étapes pour reproduire
   - Comportement attendu vs réel
   - Version du système et navigateur
   - Captures d'écran si applicable

## 💡 Proposer une Fonctionnalité

1. Vérifiez que la fonctionnalité n'a pas déjà été proposée
2. Créez une issue avec le template de fonctionnalité
3. Décrivez :
   - Le problème que cela résout
   - La solution proposée
   - Alternatives considérées
   - Impact sur les utilisateurs existants

## 📋 Checklist pour les Pull Requests

- [ ] Code testé localement
- [ ] Tests passent
- [ ] Code formaté avec black
- [ ] Imports triés avec isort
- [ ] Pas d'erreurs de linting
- [ ] Documentation mise à jour
- [ ] Messages de commit clairs
- [ ] PR liée à une issue si applicable

## 🏗️ Architecture du Projet

### Structure des Dossiers
```
school_management/
├── school_management/     # Application Django principale
├── school_system/         # Configuration du projet
├── templates/            # Templates HTML
├── static/              # Fichiers statiques
├── media/               # Fichiers média
├── tests/               # Tests (à créer)
└── docs/                # Documentation (à créer)
```

### Modèles Principaux
- `Eleve` : Gestion des élèves
- `Professeur` : Gestion des professeurs
- `Parent` : Gestion des parents
- `Classe` : Gestion des classes
- `Matiere` : Gestion des matières
- `Note` : Gestion des notes
- `Bulletin` : Gestion des bulletins

## 🔧 Outils de Développement

### Développement Local
- Django Debug Toolbar pour le débogage
- Django Extensions pour des commandes utiles
- Coverage pour mesurer la couverture de tests

### CI/CD
- GitHub Actions pour l'intégration continue
- Tests automatiques sur chaque PR
- Déploiement automatique sur la branche main

## 📞 Support

- Créez une issue pour les questions
- Consultez la documentation Django
- Vérifiez les logs dans `logs/django.log`

## 🎯 Roadmap

Consultez les issues étiquetées `enhancement` pour voir les fonctionnalités planifiées.

Merci de contribuer ! 🎉
