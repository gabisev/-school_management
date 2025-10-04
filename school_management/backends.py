from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import Eleve, Professeur, Parent

User = get_user_model()

class EleveAuthBackend(BaseBackend):
    """
    Backend d'authentification pour les élèves
    Permet la connexion avec le numéro étudiant et un mot de passe
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Chercher l'élève par son numéro étudiant
            eleve = Eleve.objects.get(numero_etudiant=username)
            user = eleve.user
            
            # Vérifier que l'élève a un objet User associé
            if user is None:
                return None
            
            # Vérifier le mot de passe
            if user.check_password(password):
                return user
        except Eleve.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class ProfesseurAuthBackend(BaseBackend):
    """
    Backend d'authentification pour les professeurs
    Permet la connexion avec le nom d'utilisateur et un mot de passe
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Chercher le professeur par son nom d'utilisateur
            professeur = Professeur.objects.get(user__username=username)
            user = professeur.user
            
            # Vérifier le mot de passe
            if user.check_password(password):
                return user
        except Professeur.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class AdminAuthBackend(BaseBackend):
    """
    Backend d'authentification pour les administrateurs
    Authentification standard Django
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and (user.is_staff or user.is_superuser):
                return user
        except User.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class ParentAuthBackend(BaseBackend):
    """
    Backend d'authentification pour les parents
    Permet la connexion avec le nom d'utilisateur et un mot de passe
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Chercher le parent par son nom d'utilisateur
            parent = Parent.objects.get(user__username=username)
            user = parent.user
            
            # Vérifier que le parent a un objet User associé
            if user is None:
                return None
            
            # Vérifier le mot de passe
            if user.check_password(password):
                return user
        except Parent.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

