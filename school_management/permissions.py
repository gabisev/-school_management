from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from functools import wraps
from .models import Eleve, Professeur


def get_user_type(user):
    """Détermine le type d'utilisateur"""
    if hasattr(user, 'eleve'):
        return 'eleve'
    elif hasattr(user, 'professeur'):
        return 'professeur'
    elif hasattr(user, 'parent'):
        return 'parent'
    elif user.is_staff or user.is_superuser:
        return 'admin'
    return None


def eleve_required(view_func):
    """Décorateur pour restreindre l'accès aux élèves uniquement"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'eleve'):
            raise PermissionDenied("Accès réservé aux élèves")
        return view_func(request, *args, **kwargs)
    return wrapper


def professeur_required(view_func):
    """Décorateur pour restreindre l'accès aux professeurs uniquement"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['professeur', 'admin']:
            raise PermissionDenied("Accès réservé aux professeurs")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Décorateur pour restreindre l'accès aux administrateurs uniquement"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Accès réservé aux administrateurs")
        return view_func(request, *args, **kwargs)
    return wrapper


class EleveRequiredMixin(LoginRequiredMixin):
    """Mixin pour restreindre l'accès aux élèves uniquement"""
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'eleve'):
            raise PermissionDenied("Accès réservé aux élèves")
        return super().dispatch(request, *args, **kwargs)


class ProfesseurRequiredMixin(LoginRequiredMixin):
    """Mixin pour restreindre l'accès aux professeurs et admins"""
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['professeur', 'admin']:
            raise PermissionDenied("Accès réservé aux professeurs")
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin pour restreindre l'accès aux administrateurs uniquement"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Accès réservé aux administrateurs")
        return super().dispatch(request, *args, **kwargs)


class EleveDataMixin:
    """Mixin pour filtrer les données selon l'élève connecté"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne voit que ses propres données
            if hasattr(queryset.model, 'eleve'):
                return queryset.filter(eleve=self.request.user.eleve)
            else:
                # Si le modèle n'a pas de champ eleve, interdire l'accès
                raise PermissionDenied("Accès non autorisé")
        
        return queryset


class ProfesseurDataMixin:
    """Mixin pour filtrer les données selon le professeur connecté"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_type = get_user_type(self.request.user)
        
        if user_type == 'professeur':
            professeur = self.request.user.professeur
            
            # Filtrer selon le type de modèle
            if hasattr(queryset.model, 'professeur'):
                return queryset.filter(professeur=professeur)
            elif hasattr(queryset.model, 'classe'):
                # Pour les modèles avec classe, filtrer par les classes du professeur
                return queryset.filter(classe__in=professeur.classes.all())
            elif hasattr(queryset.model, 'matiere'):
                # Pour les modèles avec matière, filtrer par les matières du professeur
                return queryset.filter(matiere__in=professeur.matieres.all())
            elif hasattr(queryset.model, 'eleve'):
                # Pour les notes/absences, filtrer par les élèves des classes du professeur
                return queryset.filter(eleve__classe__in=professeur.classes.all())
        
        return queryset


def check_eleve_access(user, eleve):
    """Vérifie si l'utilisateur peut accéder aux données de cet élève"""
    user_type = get_user_type(user)
    
    if user_type == 'eleve':
        # Un élève ne peut voir que ses propres données
        if user.eleve != eleve:
            raise PermissionDenied("Vous ne pouvez accéder qu'à vos propres données")
    elif user_type == 'professeur':
        # Un professeur ne peut voir que les élèves de ses classes
        if eleve.classe not in user.professeur.classes.all():
            raise PermissionDenied("Vous ne pouvez accéder qu'aux données de vos élèves")
    elif user_type != 'admin':
        raise PermissionDenied("Accès non autorisé")


def check_classe_access(user, classe):
    """Vérifie si l'utilisateur peut accéder aux données de cette classe"""
    user_type = get_user_type(user)
    
    if user_type == 'eleve':
        # Un élève ne peut voir que sa propre classe
        if user.eleve.classe != classe:
            raise PermissionDenied("Vous ne pouvez accéder qu'aux données de votre classe")
    elif user_type == 'professeur':
        # Un professeur ne peut voir que ses classes
        if classe not in user.professeur.classes.all():
            raise PermissionDenied("Vous ne pouvez accéder qu'aux données de vos classes")
    elif user_type != 'admin':
        raise PermissionDenied("Accès non autorisé")


def check_evaluation_access(user, evaluation):
    """Vérifie si l'utilisateur peut accéder aux données de cette évaluation"""
    user_type = get_user_type(user)
    
    if user_type == 'eleve':
        # Un élève ne peut voir que les évaluations de sa classe
        if user.eleve.classe != evaluation.classe:
            raise PermissionDenied("Vous ne pouvez accéder qu'aux évaluations de votre classe")
    elif user_type == 'professeur':
        # Un professeur ne peut voir que ses évaluations
        if evaluation.professeur != user.professeur:
            raise PermissionDenied("Vous ne pouvez accéder qu'à vos propres évaluations")
    elif user_type != 'admin':
        raise PermissionDenied("Accès non autorisé")

