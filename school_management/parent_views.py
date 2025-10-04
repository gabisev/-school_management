from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Eleve, Note, Absence, Communication, Evaluation, Matiere, Conversation, Message


@login_required
def parent_dashboard(request):
    """Tableau de bord personnalisé pour les parents"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    if user_type != 'parent':
        raise PermissionDenied("Accès réservé aux parents")
    
    try:
        parent = request.user.parent
    except:
        raise PermissionDenied("Profil parent non trouvé")
    
    # Récupérer tous les enfants du parent
    enfants = parent.eleves.all()
    
    # Statistiques générales
    total_enfants = enfants.count()
    total_absences = Absence.objects.filter(eleve__in=enfants).count()
    total_notes = Note.objects.filter(eleve__in=enfants).count()
    
    # Absences récentes
    absences_recentes = Absence.objects.filter(
        eleve__in=enfants
    ).order_by('-date_debut')[:5]
    
    # Notes récentes
    notes_recentes = Note.objects.filter(
        eleve__in=enfants
    ).select_related('evaluation', 'evaluation__matiere').order_by('-date_saisie')[:10]
    
    # Communications récentes
    communications_recentes = Communication.objects.filter(
        Q(destinataires__in=['TOUS', 'PARENTS']) |
        Q(destinataires='CLASSE', classe_cible__in=enfants.values_list('classe', flat=True))
    ).filter(active=True).order_by('-date_creation')[:5]
    
    # Données de messagerie
    conversations_count = Conversation.objects.filter(
        participants__user=request.user,
        participants__actif=True,
        active=True
    ).count()
    
    unread_messages_count = Message.objects.filter(
        conversation__participants__user=request.user,
        conversation__participants__actif=True,
        lu=False
    ).exclude(expediteur=request.user).count()
    
    recent_conversations = Conversation.objects.filter(
        participants__user=request.user,
        participants__actif=True,
        active=True
    ).order_by('-date_modification')[:5]
    
    # Moyennes par enfant et par matière
    moyennes_par_enfant = {}
    for enfant in enfants:
        moyennes_par_matiere = {}
        notes_enfant = Note.objects.filter(eleve=enfant, note__isnull=False)
        
        for note in notes_enfant:
            matiere = note.evaluation.matiere
            if matiere not in moyennes_par_matiere:
                moyennes_par_matiere[matiere] = []
            moyennes_par_matiere[matiere].append(float(note.note))
        
        # Calculer les moyennes
        for matiere, notes in moyennes_par_matiere.items():
            moyennes_par_matiere[matiere] = round(sum(notes) / len(notes), 2)
        
        moyennes_par_enfant[enfant] = moyennes_par_matiere
    
    context = {
        'parent': parent,
        'enfants': enfants,
        'total_enfants': total_enfants,
        'total_absences': total_absences,
        'total_notes': total_notes,
        'absences_recentes': absences_recentes,
        'notes_recentes': notes_recentes,
        'communications_recentes': communications_recentes,
        'moyennes_par_enfant': moyennes_par_enfant,
        'conversations_count': conversations_count,
        'unread_messages_count': unread_messages_count,
        'recent_conversations': recent_conversations,
    }
    
    return render(request, 'school_management/dashboards/parent.html', context)


@login_required
def parent_enfant_detail(request, eleve_id):
    """Détail d'un enfant pour un parent"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    if user_type != 'parent':
        raise PermissionDenied("Accès réservé aux parents")
    
    try:
        parent = request.user.parent
        enfant = get_object_or_404(Eleve, id=eleve_id)
        
        # Vérifier que l'enfant appartient au parent
        if enfant not in parent.eleves.all():
            raise PermissionDenied("Cet enfant ne vous appartient pas")
            
    except:
        raise PermissionDenied("Profil parent non trouvé")
    
    # Récupérer les données de l'enfant
    notes = Note.objects.filter(eleve=enfant).select_related('evaluation', 'evaluation__matiere').order_by('-date_saisie')
    absences = Absence.objects.filter(eleve=enfant).order_by('-date_debut')
    evaluations = Evaluation.objects.filter(classe=enfant.classe).order_by('-date_evaluation')
    
    # Calculer les moyennes par matière
    moyennes_par_matiere = {}
    for note in notes.filter(note__isnull=False):
        matiere = note.evaluation.matiere
        if matiere not in moyennes_par_matiere:
            moyennes_par_matiere[matiere] = []
        moyennes_par_matiere[matiere].append(float(note.note))
    
    # Calculer les moyennes finales
    for matiere, notes_list in moyennes_par_matiere.items():
        moyennes_par_matiere[matiere] = round(sum(notes_list) / len(notes_list), 2)
    
    # Statistiques
    total_notes = notes.count()
    notes_validees = notes.filter(note__isnull=False).count()
    total_absences = absences.count()
    absences_justifiees = absences.filter(justifiee=True).count()
    
    context = {
        'parent': parent,
        'enfant': enfant,
        'notes': notes,
        'absences': absences,
        'evaluations': evaluations,
        'moyennes_par_matiere': moyennes_par_matiere,
        'total_notes': total_notes,
        'notes_validees': notes_validees,
        'total_absences': total_absences,
        'absences_justifiees': absences_justifiees,
    }
    
    return render(request, 'school_management/parent/enfant_detail.html', context)


@login_required
def parent_notes(request):
    """Vue des notes pour les parents"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    if user_type != 'parent':
        raise PermissionDenied("Accès réservé aux parents")
    
    try:
        parent = request.user.parent
    except:
        raise PermissionDenied("Profil parent non trouvé")
    
    # Récupérer tous les enfants du parent
    enfants = parent.eleves.all()
    
    # Récupérer toutes les notes des enfants
    notes = Note.objects.filter(
        eleve__in=enfants
    ).select_related('eleve', 'evaluation', 'evaluation__matiere').order_by('-date_saisie')
    
    # Filtrer par enfant si spécifié
    eleve_id = request.GET.get('eleve')
    if eleve_id:
        try:
            eleve = enfants.get(id=eleve_id)
            notes = notes.filter(eleve=eleve)
        except:
            pass
    
    # Filtrer par matière si spécifiée
    matiere_id = request.GET.get('matiere')
    if matiere_id:
        notes = notes.filter(evaluation__matiere_id=matiere_id)
    
    # Pagination
    paginator = Paginator(notes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer les matières pour le filtre
    matieres = Matiere.objects.filter(
        evaluations__notes__eleve__in=enfants
    ).distinct().order_by('nom')
    
    context = {
        'parent': parent,
        'enfants': enfants,
        'matieres': matieres,
        'page_obj': page_obj,
        'notes': page_obj,
        'selected_eleve': eleve_id,
        'selected_matiere': matiere_id,
    }
    
    return render(request, 'school_management/parent/notes.html', context)


@login_required
def parent_absences(request):
    """Vue des absences pour les parents"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    if user_type != 'parent':
        raise PermissionDenied("Accès réservé aux parents")
    
    try:
        parent = request.user.parent
    except:
        raise PermissionDenied("Profil parent non trouvé")
    
    # Récupérer tous les enfants du parent
    enfants = parent.eleves.all()
    
    # Récupérer toutes les absences des enfants
    absences = Absence.objects.filter(
        eleve__in=enfants
    ).select_related('eleve').order_by('-date_debut')
    
    # Filtrer par enfant si spécifié
    eleve_id = request.GET.get('eleve')
    if eleve_id:
        try:
            eleve = enfants.get(id=eleve_id)
            absences = absences.filter(eleve=eleve)
        except:
            pass
    
    # Filtrer par statut de justification
    justifiee = request.GET.get('justifiee')
    if justifiee == 'true':
        absences = absences.filter(justifiee=True)
    elif justifiee == 'false':
        absences = absences.filter(justifiee=False)
    
    # Pagination
    paginator = Paginator(absences, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'parent': parent,
        'enfants': enfants,
        'page_obj': page_obj,
        'absences': page_obj,
        'selected_eleve': eleve_id,
        'selected_justifiee': justifiee,
    }
    
    return render(request, 'school_management/parent/absences.html', context)


