#!/usr/bin/env python
"""
Script d'initialisation pour les développeurs
Usage: python setup_dev.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Échec")
        print(f"Erreur: {e.stderr}")
        return False

def check_python_version():
    """Vérifie la version de Python"""
    print("🐍 Vérification de la version Python...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        return False
    print(f"✅ Python {sys.version.split()[0]} détecté")
    return True

def create_virtual_environment():
    """Crée un environnement virtuel"""
    if os.path.exists("venv"):
        print("📁 Environnement virtuel existant détecté")
        return True
    
    return run_command("python -m venv venv", "Création de l'environnement virtuel")

def install_dependencies():
    """Installe les dépendances"""
    # Déterminer la commande pip selon l'OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_cmd = "venv/bin/pip"
    
    commands = [
        (f"{pip_cmd} install --upgrade pip", "Mise à jour de pip"),
        (f"{pip_cmd} install -r requirements-dev.txt", "Installation des dépendances de développement"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def setup_environment():
    """Configure l'environnement"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("📄 Fichier .env existant détecté")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("📄 Fichier .env créé à partir de env.example")
        print("⚠️  N'oubliez pas de modifier les valeurs dans .env")
        return True
    else:
        print("❌ Fichier env.example non trouvé")
        return False

def run_migrations():
    """Exécute les migrations"""
    # Déterminer la commande python selon l'OS
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"
    
    commands = [
        (f"{python_cmd} manage.py makemigrations", "Création des migrations"),
        (f"{python_cmd} manage.py migrate", "Exécution des migrations"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def create_superuser():
    """Crée un superutilisateur"""
    print("👤 Création du superutilisateur...")
    print("   Utilisateur: admin")
    print("   Email: admin@example.com")
    print("   Mot de passe: admin123")
    
    # Déterminer la commande python selon l'OS
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"
    
    create_user_script = """
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé avec succès')
else:
    print('Superutilisateur existe déjà')
"""
    
    try:
        result = subprocess.run(
            f"{python_cmd} manage.py shell",
            input=create_user_script,
            shell=True,
            text=True,
            capture_output=True
        )
        if result.returncode == 0:
            print("✅ Superutilisateur créé")
            return True
        else:
            print("❌ Erreur lors de la création du superutilisateur")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def collect_static():
    """Collecte les fichiers statiques"""
    # Déterminer la commande python selon l'OS
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"
    
    return run_command(f"{python_cmd} manage.py collectstatic --noinput", "Collecte des fichiers statiques")

def main():
    """Fonction principale"""
    print("🚀 Configuration de l'environnement de développement")
    print("=" * 50)
    
    steps = [
        ("Vérification Python", check_python_version),
        ("Environnement virtuel", create_virtual_environment),
        ("Dépendances", install_dependencies),
        ("Configuration", setup_environment),
        ("Migrations", run_migrations),
        ("Superutilisateur", create_superuser),
        ("Fichiers statiques", collect_static),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        if not step_func():
            print(f"\n❌ Échec à l'étape: {step_name}")
            print("Veuillez corriger les erreurs et relancer le script")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Configuration terminée avec succès!")
    print("\n📋 Prochaines étapes:")
    print("1. Activez l'environnement virtuel:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Lancez le serveur de développement:")
    print("   python manage.py runserver")
    print("3. Accédez à http://127.0.0.1:8000")
    print("4. Connectez-vous avec admin/admin123")

if __name__ == "__main__":
    main()
