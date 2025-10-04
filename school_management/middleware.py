from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages


class UserTypeRedirectMiddleware:
    """
    Middleware pour rediriger automatiquement les utilisateurs vers leur tableau de bord approprié
    selon leur type (élève, professeur, admin) après connexion.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Si l'utilisateur est authentifié et accède à la page d'accueil principale
        if (request.user.is_authenticated and 
            request.path == reverse('school_management:dashboard')):
            
            # Déterminer le type d'utilisateur et rediriger vers le bon dashboard
            user_type = self.get_user_type(request.user)
            
            if user_type == 'eleve':
                return redirect('school_management:eleve_dashboard')
            elif user_type == 'professeur':
                return redirect('school_management:professeur_dashboard')
            elif user_type == 'parent':
                return redirect('school_management:parent_dashboard')
            elif user_type == 'admin':
                # Les admins restent sur le dashboard principal
                pass
        
        # Vérifier les autorisations d'accès aux dashboards spécialisés
        if request.user.is_authenticated:
            user_type = self.get_user_type(request.user)
            
            # Empêcher les élèves d'accéder au dashboard professeur
            if (request.path == reverse('school_management:professeur_dashboard') and 
                user_type != 'professeur' and user_type != 'admin'):
                messages.error(request, 'Accès non autorisé à cette section.')
                return redirect('school_management:eleve_dashboard' if user_type == 'eleve' 
                              else 'school_management:dashboard')
            
            # Empêcher les professeurs d'accéder au dashboard élève
            if (request.path == reverse('school_management:eleve_dashboard') and 
                user_type != 'eleve' and user_type != 'admin'):
                messages.error(request, 'Accès non autorisé à cette section.')
                return redirect('school_management:professeur_dashboard' if user_type == 'professeur' 
                              else 'school_management:parent_dashboard' if user_type == 'parent'
                              else 'school_management:dashboard')
            
            # Empêcher l'accès non autorisé au dashboard parent
            if (request.path == reverse('school_management:parent_dashboard') and 
                user_type != 'parent' and user_type != 'admin'):
                messages.error(request, 'Accès non autorisé à cette section.')
                return redirect('school_management:eleve_dashboard' if user_type == 'eleve'
                              else 'school_management:professeur_dashboard' if user_type == 'professeur'
                              else 'school_management:dashboard')
        
        return response
    
    def get_user_type(self, user):
        """Détermine le type d'utilisateur"""
        try:
            if hasattr(user, 'eleve'):
                return 'eleve'
            elif hasattr(user, 'professeur'):
                return 'professeur'
            elif hasattr(user, 'parent'):
                return 'parent'
            elif user.is_staff or user.is_superuser:
                return 'admin'
        except:
            pass
        return None

