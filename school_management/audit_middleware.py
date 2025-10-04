"""
Middleware pour enregistrer automatiquement les logs d'audit
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .audit_utils import log_login, log_logout


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware pour enregistrer automatiquement les logs d'audit
    """
    
    def process_request(self, request):
        """Traite la requête et stocke l'objet request pour les signaux"""
        # Stocker l'objet request pour l'utiliser dans les signaux
        self.request = request
        return None


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Signal pour enregistrer les connexions"""
    log_login(user, request)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Signal pour enregistrer les déconnexions"""
    log_logout(user, request)






