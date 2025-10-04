"""
Utilitaires pour l'audit des actions des utilisateurs
"""
from django.contrib.auth.models import User
from .models import AuditLog


def log_user_action(user, action, model_name, object_id=None, object_repr="", details="", request=None):
    """
    Enregistre une action utilisateur dans les logs d'audit
    
    Args:
        user: L'utilisateur qui effectue l'action
        action: Le type d'action (CREATE, UPDATE, DELETE, VIEW, etc.)
        model_name: Le nom du modèle concerné
        object_id: L'ID de l'objet concerné (optionnel)
        object_repr: La représentation textuelle de l'objet
        details: Détails supplémentaires
        request: L'objet request pour récupérer IP et User-Agent
    """
    try:
        ip_address = None
        user_agent = ""
        
        if request:
            # Récupérer l'adresse IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Récupérer le User-Agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # En cas d'erreur, on ne veut pas interrompre le processus principal
        print(f"Erreur lors de l'enregistrement du log d'audit: {e}")


def log_login(user, request=None):
    """Enregistre une connexion"""
    log_user_action(
        user=user,
        action='LOGIN',
        model_name='User',
        object_id=user.id,
        object_repr=f"{user.get_full_name()} ({user.username})",
        details=f"Connexion de {user.get_full_name()}",
        request=request
    )


def log_logout(user, request=None):
    """Enregistre une déconnexion"""
    log_user_action(
        user=user,
        action='LOGOUT',
        model_name='User',
        object_id=user.id,
        object_repr=f"{user.get_full_name()} ({user.username})",
        details=f"Déconnexion de {user.get_full_name()}",
        request=request
    )


def log_model_action(user, action, instance, request=None, details=""):
    """
    Enregistre une action sur un modèle
    
    Args:
        user: L'utilisateur qui effectue l'action
        action: Le type d'action (CREATE, UPDATE, DELETE, VIEW)
        instance: L'instance du modèle
        request: L'objet request
        details: Détails supplémentaires
    """
    model_name = instance._meta.verbose_name or instance._meta.model_name
    object_repr = str(instance)
    
    log_user_action(
        user=user,
        action=action,
        model_name=model_name,
        object_id=instance.pk,
        object_repr=object_repr,
        details=details,
        request=request
    )


def log_notes_save(user, evaluation, notes_count, request=None):
    """Enregistre la saisie de notes"""
    log_user_action(
        user=user,
        action='NOTE_SAVE',
        model_name='Note',
        object_id=evaluation.pk,
        object_repr=f"Évaluation: {evaluation.titre}",
        details=f"Saisie de {notes_count} notes pour l'évaluation '{evaluation.titre}'",
        request=request
    )






