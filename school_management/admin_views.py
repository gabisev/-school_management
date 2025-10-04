from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Avg
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User

from .models import (
    Eleve, Professeur, Parent, Classe, Matiere, 
    Evaluation, Note, Absence, Bulletin, Communication
)
from .permissions import get_user_type
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm,
    EleveUserForm, ProfesseurUserForm, ParentUserForm
)


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """Vue du tableau de bord administrateur personnalisé"""
    template_name = 'school_management/admin/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        context['total_eleves'] = Eleve.objects.count()
        context['total_professeurs'] = Professeur.objects.count()
        context['total_parents'] = Parent.objects.count()
        context['total_classes'] = Classe.objects.count()
        context['total_matieres'] = Matiere.objects.count()
        
        # Statistiques des évaluations et notes
        context['total_evaluations'] = Evaluation.objects.count()
        context['total_notes'] = Note.objects.count()
        context['total_bulletins'] = Bulletin.objects.count()
        
        # Statistiques des absences
        context['total_absences'] = Absence.objects.count()
        context['absences_non_justifiees'] = Absence.objects.filter(justifiee=False).count()
        
        # Statistiques des communications
        context['total_communications'] = Communication.objects.count()
        context['communications_recentes'] = Communication.objects.filter(
            date_creation__gte=timezone.now().replace(day=1)
        ).count()
        
        # Moyennes par classe
        classes_stats = []
        for classe in Classe.objects.all():
            bulletins = Bulletin.objects.filter(classe=classe, statut='VALIDE')
            if bulletins.exists():
                moyenne_classe = bulletins.aggregate(avg=Avg('moyenne_generale'))['avg']
                classes_stats.append({
                    'classe': classe,
                    'moyenne': round(moyenne_classe, 2) if moyenne_classe else 0,
                    'effectif': classe.eleves.count(),
                    'bulletins_valides': bulletins.count()
                })
        
        context['classes_stats'] = sorted(classes_stats, key=lambda x: x['moyenne'], reverse=True)
        
        # Top 5 des meilleurs élèves
        top_eleves = Bulletin.objects.filter(
            statut='VALIDE',
            moyenne_generale__isnull=False
        ).order_by('-moyenne_generale')[:5]
        
        context['top_eleves'] = top_eleves
        
        # Répartition par trimestre
        bulletins_par_trimestre = Bulletin.objects.values('trimestre').annotate(
            count=Count('id')
        ).order_by('trimestre')
        
        context['bulletins_par_trimestre'] = bulletins_par_trimestre
        
        # Professeurs avec le plus d'évaluations
        profs_actifs = Professeur.objects.annotate(
            nb_evaluations=Count('evaluations')
        ).order_by('-nb_evaluations')[:5]
        
        context['profs_actifs'] = profs_actifs
        
        return context


@login_required
def admin_statistics(request):
    """Vue pour les statistiques détaillées"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    # Statistiques détaillées par classe
    classes_detailed = []
    for classe in Classe.objects.all():
        eleves_count = classe.eleves.count()
        bulletins_count = Bulletin.objects.filter(classe=classe).count()
        bulletins_valides = Bulletin.objects.filter(classe=classe, statut='VALIDE').count()
        
        # Moyenne de la classe
        bulletins = Bulletin.objects.filter(classe=classe, statut='VALIDE')
        moyenne_classe = bulletins.aggregate(avg=Avg('moyenne_generale'))['avg']
        
        # Répartition des notes
        if bulletins.exists():
            excellent = bulletins.filter(moyenne_generale__gte=16).count()
            bien = bulletins.filter(moyenne_generale__gte=14, moyenne_generale__lt=16).count()
            assez_bien = bulletins.filter(moyenne_generale__gte=12, moyenne_generale__lt=14).count()
            passable = bulletins.filter(moyenne_generale__gte=10, moyenne_generale__lt=12).count()
            insuffisant = bulletins.filter(moyenne_generale__lt=10).count()
        else:
            excellent = bien = assez_bien = passable = insuffisant = 0
        
        classes_detailed.append({
            'classe': classe,
            'eleves_count': eleves_count,
            'bulletins_count': bulletins_count,
            'bulletins_valides': bulletins_valides,
            'moyenne_classe': round(moyenne_classe, 2) if moyenne_classe else 0,
            'excellent': excellent,
            'bien': bien,
            'assez_bien': assez_bien,
            'passable': passable,
            'insuffisant': insuffisant,
            'prof_principal': classe.prof_principal
        })
    
    context = {
        'classes_detailed': classes_detailed,
        'total_classes': Classe.objects.count(),
        'total_eleves': Eleve.objects.count(),
        'total_bulletins': Bulletin.objects.count(),
        'bulletins_valides': Bulletin.objects.filter(statut='VALIDE').count(),
    }
    
    return render(request, 'school_management/admin/statistics.html', context)


@login_required
def admin_users_management(request):
    """Vue pour la gestion des utilisateurs"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    # Statistiques des utilisateurs
    eleves_sans_user = Eleve.objects.filter(user__isnull=True).count()
    professeurs_sans_user = Professeur.objects.filter(user__isnull=True).count()
    parents_sans_user = Parent.objects.filter(user__isnull=True).count()
    
    # Utilisateurs récents - afficher plus d'utilisateurs pour voir tous les types
    from django.contrib.auth.models import User
    recent_users = User.objects.select_related(
        'eleve', 'professeur', 'parent'
    ).order_by('-date_joined')[:50]
    
    # Utilisateurs par type pour un meilleur affichage
    professeur_users = User.objects.filter(professeur__isnull=False).select_related('professeur').order_by('-date_joined')[:10]
    eleve_users = User.objects.filter(eleve__isnull=False).select_related('eleve').order_by('-date_joined')[:10]
    parent_users = User.objects.filter(parent__isnull=False).select_related('parent').order_by('-date_joined')[:10]
    
    context = {
        'eleves_sans_user': eleves_sans_user,
        'professeurs_sans_user': professeurs_sans_user,
        'parents_sans_user': parents_sans_user,
        'recent_users': recent_users,
        'professeur_users': professeur_users,
        'eleve_users': eleve_users,
        'parent_users': parent_users,
        'total_users': User.objects.count(),
    }
    
    return render(request, 'school_management/admin/users_management.html', context)


@login_required
def admin_prof_principal_management(request):
    """Vue pour la gestion des professeurs principaux"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    if request.method == 'POST':
        classe_id = request.POST.get('classe_id')
        prof_id = request.POST.get('prof_id')
        
        # Vérifier si c'est une requête AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            classe = Classe.objects.get(id=classe_id)
            if prof_id:
                prof = Professeur.objects.get(id=prof_id)
                
                # Vérifier si le professeur est déjà principal d'une autre classe
                existing_classe = Classe.objects.filter(
                    prof_principal=prof
                ).exclude(pk=classe.pk)
                
                if existing_classe.exists():
                    existing_classe_nom = existing_classe.first().nom
                    error_msg = f"Le professeur {prof.user.get_full_name()} est déjà professeur principal de la classe {existing_classe_nom}. Un professeur ne peut être principal que d'une seule classe."
                    messages.error(request, error_msg)
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': error_msg})
                    return redirect('school_management:admin_prof_principal_management')
                
                classe.prof_principal = prof
                action = f'Professeur principal {prof.user.get_full_name()} assigné avec succès à la classe {classe.nom}.'
            else:
                classe.prof_principal = None
                action = f'Professeur principal retiré avec succès de la classe {classe.nom}.'
            
            # Valider le modèle avant de sauvegarder
            classe.clean()
            classe.save()
            
            messages.success(request, action)
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': action,
                    'classe_nom': classe.nom,
                    'prof_nom': classe.prof_principal.user.get_full_name() if classe.prof_principal else None
                })
                
        except Classe.DoesNotExist:
            error_msg = 'Classe introuvable.'
            messages.error(request, error_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
        except Professeur.DoesNotExist:
            error_msg = 'Professeur introuvable.'
            messages.error(request, error_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
        except ValidationError as e:
            error_msg = str(e)
            messages.error(request, error_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
        except Exception as e:
            error_msg = f'Erreur lors de l\'assignation: {str(e)}'
            messages.error(request, error_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
    
    # Récupérer toutes les classes avec leurs professeurs principaux
    classes = Classe.objects.all().order_by('niveau', 'nom')
    
    # Récupérer tous les professeurs
    professeurs = Professeur.objects.all().order_by('user__last_name', 'user__first_name')
    
    # Statistiques
    classes_avec_prof_principal = Classe.objects.filter(prof_principal__isnull=False).count()
    classes_sans_prof_principal = Classe.objects.filter(prof_principal__isnull=True).count()
    
    # Professeurs avec plusieurs classes
    profs_multiples_classes = Professeur.objects.annotate(
        nb_classes=Count('classes_principales')
    ).filter(nb_classes__gt=1)
    
    context = {
        'classes': classes,
        'professeurs': professeurs,
        'classes_avec_prof_principal': classes_avec_prof_principal,
        'classes_sans_prof_principal': classes_sans_prof_principal,
        'profs_multiples_classes': profs_multiples_classes,
        'total_classes': Classe.objects.count(),
        'total_professeurs': Professeur.objects.count(),
    }
    
    return render(request, 'school_management/admin/prof_principal_management.html', context)


# ===== GESTION DES UTILISATEURS =====

@login_required
def admin_user_management(request):
    """Vue pour la gestion complète des utilisateurs"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    # Statistiques
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Utilisateurs sans compte
    eleves_sans_user = Eleve.objects.filter(user__isnull=True).count()
    professeurs_sans_user = Professeur.objects.filter(user__isnull=True).count()
    parents_sans_user = Parent.objects.filter(user__isnull=True).count()
    
    # Utilisateurs récents
    recent_users = User.objects.select_related(
        'eleve', 'professeur', 'parent'
    ).order_by('-date_joined')[:20]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'eleves_sans_user': eleves_sans_user,
        'professeurs_sans_user': professeurs_sans_user,
        'parents_sans_user': parents_sans_user,
        'recent_users': recent_users,
    }
    
    return render(request, 'school_management/admin/user_management.html', context)


@login_required
def admin_create_user(request):
    """Vue pour créer un nouvel utilisateur"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Utilisateur {user.username} créé avec succès.')
            return redirect('school_management:admin_user_management')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Créer un nouvel utilisateur'
    }
    
    return render(request, 'school_management/admin/user_form.html', context)


@login_required
def admin_edit_user(request, user_id):
    """Vue pour modifier un utilisateur"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Utilisateur {user.username} modifié avec succès.')
            return redirect('school_management:admin_user_management')
    else:
        form = CustomUserChangeForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Modifier l\'utilisateur {user.username}'
    }
    
    return render(request, 'school_management/admin/user_form.html', context)


@login_required
def admin_create_eleve_user(request, eleve_id):
    """Vue pour créer un compte utilisateur pour un élève"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    eleve = get_object_or_404(Eleve, id=eleve_id)
    
    if request.method == 'POST':
        form = EleveUserForm(request.POST, request.FILES, user=eleve.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Compte utilisateur créé pour l\'élève {eleve.nom} {eleve.prenom}.')
            return redirect('school_management:admin_user_management')
    else:
        form = EleveUserForm(user=eleve.user)
        # Pré-remplir avec les données de l'élève
        form.fields['username'].initial = f"{eleve.prenom.lower()}.{eleve.nom.lower()}"
        form.fields['first_name'].initial = eleve.prenom
        form.fields['last_name'].initial = eleve.nom
        form.fields['email'].initial = eleve.email
    
    context = {
        'form': form,
        'eleve': eleve,
        'title': f'Créer un compte pour {eleve.prenom} {eleve.nom}'
    }
    
    return render(request, 'school_management/admin/eleve_user_form.html', context)


@login_required
def admin_edit_eleve_user(request, eleve_id):
    """Vue pour modifier un élève et son compte utilisateur"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    eleve = get_object_or_404(Eleve, id=eleve_id)
    
    if request.method == 'POST':
        form = EleveUserForm(request.POST, request.FILES, instance=eleve, user=eleve.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Élève {eleve.nom} {eleve.prenom} modifié avec succès.')
            return redirect('school_management:admin_user_management')
    else:
        form = EleveUserForm(instance=eleve, user=eleve.user)
    
    context = {
        'form': form,
        'eleve': eleve,
        'title': f'Modifier {eleve.prenom} {eleve.nom}'
    }
    
    return render(request, 'school_management/admin/eleve_user_form.html', context)


@login_required
def admin_create_professeur_user(request, professeur_id):
    """Vue pour créer un compte utilisateur pour un professeur"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    professeur = get_object_or_404(Professeur, id=professeur_id)
    
    if request.method == 'POST':
        form = ProfesseurUserForm(request.POST, request.FILES, user=professeur.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Compte utilisateur créé pour le professeur {professeur.nom} {professeur.prenom}.')
            return redirect('school_management:admin_user_management')
    else:
        form = ProfesseurUserForm(user=professeur.user)
        # Pré-remplir avec les données du professeur
        form.fields['username'].initial = f"{professeur.prenom.lower()}.{professeur.nom.lower()}"
        form.fields['first_name'].initial = professeur.prenom
        form.fields['last_name'].initial = professeur.nom
        form.fields['email'].initial = professeur.email
    
    context = {
        'form': form,
        'professeur': professeur,
        'title': f'Créer un compte pour {professeur.prenom} {professeur.nom}'
    }
    
    return render(request, 'school_management/admin/professeur_user_form.html', context)


@login_required
def admin_edit_professeur_user(request, professeur_id):
    """Vue pour modifier un professeur et son compte utilisateur"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    professeur = get_object_or_404(Professeur, id=professeur_id)
    
    if request.method == 'POST':
        form = ProfesseurUserForm(request.POST, request.FILES, instance=professeur, user=professeur.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Professeur {professeur.nom} {professeur.prenom} modifié avec succès.')
            return redirect('school_management:admin_user_management')
    else:
        form = ProfesseurUserForm(instance=professeur, user=professeur.user)
    
    context = {
        'form': form,
        'professeur': professeur,
        'title': f'Modifier {professeur.prenom} {professeur.nom}'
    }
    
    return render(request, 'school_management/admin/professeur_user_form.html', context)


@login_required
def admin_create_parent_user(request, parent_id):
    """Vue pour créer un compte utilisateur pour un parent"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        form = ParentUserForm(request.POST, request.FILES, user=parent.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Compte utilisateur créé pour le parent {parent.nom} {parent.prenom}.')
            return redirect('school_management:admin_user_management')
    else:
        form = ParentUserForm(user=parent.user)
        # Pré-remplir avec les données du parent
        form.fields['username'].initial = f"{parent.prenom.lower()}.{parent.nom.lower()}"
        form.fields['first_name'].initial = parent.prenom
        form.fields['last_name'].initial = parent.nom
        form.fields['email'].initial = parent.email
    
    context = {
        'form': form,
        'parent': parent,
        'title': f'Créer un compte pour {parent.prenom} {parent.nom}'
    }
    
    return render(request, 'school_management/admin/parent_user_form.html', context)


@login_required
def admin_edit_parent_user(request, parent_id):
    """Vue pour modifier un parent et son compte utilisateur"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        form = ParentUserForm(request.POST, request.FILES, instance=parent, user=parent.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Parent {parent.nom} {parent.prenom} modifié avec succès.')
            return redirect('school_management:admin_user_management')
    else:
        form = ParentUserForm(instance=parent, user=parent.user)
    
    context = {
        'form': form,
        'parent': parent,
        'title': f'Modifier {parent.prenom} {parent.nom}'
    }
    
    return render(request, 'school_management/admin/parent_user_form.html', context)


@login_required
def admin_users_without_accounts(request):
    """Vue pour afficher les utilisateurs sans compte de connexion"""
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    # Récupérer tous les utilisateurs sans compte
    eleves_sans_user = Eleve.objects.filter(user__isnull=True)
    professeurs_sans_user = Professeur.objects.filter(user__isnull=True)
    parents_sans_user = Parent.objects.filter(user__isnull=True)
    
    context = {
        'eleves_sans_user': eleves_sans_user,
        'professeurs_sans_user': professeurs_sans_user,
        'parents_sans_user': parents_sans_user,
    }
    
    return render(request, 'school_management/admin/users_without_accounts.html', context)


@login_required
def admin_reset_user_password(request, user_id):
    """Vue pour réinitialiser le mot de passe d'un utilisateur"""
    from django.contrib.auth.models import User
    from django.contrib import messages
    
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', 'password123')
        user.set_password(new_password)
        user.save()
        
        messages.success(request, f"Mot de passe réinitialisé pour {user.username}. Nouveau mot de passe: {new_password}")
        return redirect('school_management:admin_users')
    
    context = {
        'target_user': user,
    }
    
    return render(request, 'school_management/admin/reset_password.html', context)


@login_required
def admin_user_details(request, user_id):
    """Vue pour afficher les détails d'un utilisateur et ses informations de connexion"""
    from django.contrib.auth.models import User
    
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs.")
    
    user = get_object_or_404(User, id=user_id)
    
    # Déterminer le type d'utilisateur
    user_profile = None
    profile_type = "Utilisateur standard"
    
    if hasattr(user, 'professeur') and user.professeur:
        user_profile = user.professeur
        profile_type = "Professeur"
    elif hasattr(user, 'eleve') and user.eleve:
        user_profile = user.eleve
        profile_type = "Élève"
    elif hasattr(user, 'parent') and user.parent:
        user_profile = user.parent
        profile_type = "Parent"
    
    context = {
        'target_user': user,
        'user_profile': user_profile,
        'profile_type': profile_type,
    }
    
    return render(request, 'school_management/admin/user_details.html', context)

