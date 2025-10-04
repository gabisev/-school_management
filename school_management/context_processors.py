from .permissions import get_user_type


def user_context(request):
    """Ajoute le type d'utilisateur au contexte de tous les templates"""
    context = {
        'user_type': None,
        'is_eleve': False,
        'is_professeur': False,
        'is_parent': False,
        'is_admin': False,
    }
    
    if request.user.is_authenticated:
        user_type = get_user_type(request.user)
        context.update({
            'user_type': user_type,
            'is_eleve': user_type == 'eleve',
            'is_professeur': user_type == 'professeur',
            'is_parent': user_type == 'parent',
            'is_admin': user_type == 'admin',
        })
    
    return context

