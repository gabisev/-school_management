from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views.generic import ListView, DetailView, UpdateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone

from .models import (
    Bulletin, NoteBulletin, Eleve, Classe, Matiere, 
    Note, Evaluation, Professeur, Parent
)
from .forms import BulletinForm, NoteBulletinFormSet
from .permissions import get_user_type


# ===== VUES POUR ÉLÈVES ET PARENTS =====

class BulletinListView(LoginRequiredMixin, ListView):
    """Vue pour lister les bulletins d'un élève ou d'un parent"""
    model = Bulletin
    template_name = 'school_management/bulletin/list.html'
    context_object_name = 'bulletins'
    paginate_by = 10

    def get_queryset(self):
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # L'élève voit ses propres bulletins
            return Bulletin.objects.filter(
                eleve__user=self.request.user
            ).select_related('classe', 'eleve').order_by('-trimestre', '-date_creation')
        
        elif user_type == 'parent':
            # Le parent voit les bulletins de ses enfants
            parent = get_object_or_404(Parent, user=self.request.user)
            enfants_ids = parent.get_enfants().values_list('id', flat=True)
            return Bulletin.objects.filter(
                eleve_id__in=enfants_ids
            ).select_related('classe', 'eleve').order_by('-trimestre', '-date_creation')
        
        else:
            # Autres types d'utilisateurs (admin, prof)
            return Bulletin.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'parent':
            parent = get_object_or_404(Parent, user=self.request.user)
            context['enfants'] = parent.get_enfants()
        
        return context


class BulletinDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher un bulletin en détail"""
    model = Bulletin
    template_name = 'school_management/bulletin/detail.html'
    context_object_name = 'bulletin'

    def get_object(self):
        bulletin = get_object_or_404(Bulletin, pk=self.kwargs['pk'])
        user_type = get_user_type(self.request.user)
        
        # Vérifier les permissions
        if user_type == 'eleve':
            if bulletin.eleve.user != self.request.user:
                raise PermissionDenied("Vous ne pouvez voir que vos propres bulletins.")
        
        elif user_type == 'parent':
            parent = get_object_or_404(Parent, user=self.request.user)
            if bulletin.eleve not in parent.get_enfants():
                raise PermissionDenied("Vous ne pouvez voir que les bulletins de vos enfants.")
        
        elif user_type == 'professeur':
            # Le professeur principal peut voir tous les bulletins de sa classe
            if not (hasattr(self.request.user, 'professeur') and 
                   bulletin.classe.prof_principal == self.request.user.professeur):
                raise PermissionDenied("Seul le professeur principal peut voir ce bulletin.")
        
        elif user_type != 'admin':
            raise PermissionDenied("Accès non autorisé.")
        
        return bulletin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bulletin = self.get_object()
        
        # Ajouter les notes détaillées
        context['notes_detaillees'] = bulletin.notes_detaillees.all().order_by('matiere__nom')
        
        # Statistiques
        context['total_matieres'] = context['notes_detaillees'].count()
        context['moyenne_classe'] = bulletin.moyenne_classe
        context['effectif_classe'] = bulletin.effectif_classe
        
        return context


# ===== VUES POUR PROFESSEURS =====

class BulletinProfListView(LoginRequiredMixin, ListView):
    """Vue pour lister les bulletins d'une classe (professeur principal)"""
    model = Bulletin
    template_name = 'school_management/bulletin/prof_list.html'
    context_object_name = 'bulletins'
    paginate_by = 20

    def get_queryset(self):
        user_type = get_user_type(self.request.user)
        
        if user_type != 'professeur':
            raise PermissionDenied("Accès réservé aux professeurs.")
        
        if not hasattr(self.request.user, 'professeur'):
            raise PermissionDenied("Profil professeur non trouvé.")
        
        professeur = self.request.user.professeur
        
        # Récupérer les classes dont l'utilisateur est professeur principal
        classes_principales = Classe.objects.filter(prof_principal=professeur)
        
        if not classes_principales.exists():
            return Bulletin.objects.none()
        
        return Bulletin.objects.filter(
            classe__in=classes_principales
        ).select_related('classe', 'eleve').order_by('-trimestre', 'classe__nom', 'eleve__user__last_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self.request.user, 'professeur'):
            professeur = self.request.user.professeur
            context['classes_principales'] = Classe.objects.filter(prof_principal=professeur)
        
        return context


class BulletinUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un bulletin (professeur principal uniquement)"""
    model = Bulletin
    form_class = BulletinForm
    template_name = 'school_management/bulletin/update.html'
    context_object_name = 'bulletin'

    def get_object(self):
        bulletin = get_object_or_404(Bulletin, pk=self.kwargs['pk'])
        
        # Vérifier que l'utilisateur peut modifier ce bulletin
        if not bulletin.peut_etre_modifie_par(self.request.user):
            raise PermissionDenied("Vous n'avez pas le droit de modifier ce bulletin.")
        
        return bulletin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bulletin = self.get_object()
        
        # Ajouter le formset pour les notes détaillées
        if self.request.POST:
            context['notes_formset'] = NoteBulletinFormSet(
                self.request.POST, 
                queryset=bulletin.notes_detaillees.all()
            )
        else:
            context['notes_formset'] = NoteBulletinFormSet(
                queryset=bulletin.notes_detaillees.all()
            )
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        notes_formset = context['notes_formset']
        
        if notes_formset.is_valid():
            # Sauvegarder le bulletin
            bulletin = form.save(commit=False)
            bulletin.date_modification = timezone.now()
            bulletin.save()
            
            # Sauvegarder les notes détaillées
            notes_formset.instance = bulletin
            notes_formset.save()
            
            # Recalculer automatiquement tous les champs
            bulletin.recalculer_tous_les_champs()
            
            messages.success(
                self.request, 
                f'Bulletin de {bulletin.eleve.nom_complet} mis à jour avec succès. Moyenne: {bulletin.moyenne_generale}/20, Rang: {bulletin.rang}/{bulletin.effectif_classe}'
            )
            
            return redirect('school_management:bulletin_prof_detail', pk=bulletin.pk)
        else:
            return self.form_invalid(form)


class BulletinProfDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher un bulletin en détail (professeur)"""
    model = Bulletin
    template_name = 'school_management/bulletin/prof_detail.html'
    context_object_name = 'bulletin'

    def get_object(self):
        bulletin = get_object_or_404(Bulletin, pk=self.kwargs['pk'])
        
        # Vérifier que l'utilisateur peut voir ce bulletin
        if not bulletin.peut_etre_modifie_par(self.request.user):
            raise PermissionDenied("Vous n'avez pas le droit de voir ce bulletin.")
        
        return bulletin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bulletin = self.get_object()
        
        # Ajouter les notes détaillées
        context['notes_detaillees'] = bulletin.notes_detaillees.all().order_by('matiere__nom')
        
        # Statistiques
        context['total_matieres'] = context['notes_detaillees'].count()
        context['moyenne_classe'] = bulletin.moyenne_classe
        context['effectif_classe'] = bulletin.effectif_classe
        
        # Vérifier si le bulletin peut être modifié
        context['peut_modifier'] = bulletin.peut_etre_modifie_par(self.request.user)
        
        return context


# ===== VUES AJAX =====

@login_required
def valider_bulletin(request, pk):
    """Vue AJAX pour valider un bulletin"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    bulletin = get_object_or_404(Bulletin, pk=pk)
    
    # Vérifier les permissions
    if not bulletin.peut_etre_modifie_par(request.user):
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    # Valider le bulletin
    bulletin.statut = 'VALIDE'
    bulletin.date_validation = timezone.now()
    bulletin.valide_par = request.user
    bulletin.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Bulletin de {bulletin.eleve.nom_complet} validé avec succès.',
        'statut': bulletin.get_statut_display()
    })


@login_required
def generer_bulletin_eleve(request, eleve_id, trimestre):
    """Vue AJAX pour générer un bulletin pour un élève spécifique"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    
    # Vérifier que l'utilisateur est le professeur principal de la classe
    if not (hasattr(request.user, 'professeur') and 
           eleve.classe.prof_principal == request.user.professeur):
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    try:
        # Vérifier si toutes les évaluations sont complètes
        if not eleve.classe.prof_principal:
            return JsonResponse({'error': 'Aucun professeur principal défini'}, status=400)
        
        # Créer ou mettre à jour le bulletin
        bulletin, created = Bulletin.objects.get_or_create(
            eleve=eleve,
            classe=eleve.classe,
            annee_scolaire='2024-2025',
            trimestre=trimestre,
            defaults={
                'cree_par': request.user,
                'statut': 'BROUILLON'
            }
        )
        
        # Générer le contenu du bulletin (logique simplifiée)
        # Ici, vous pourriez appeler la même logique que dans le management command
        
        return JsonResponse({
            'success': True,
            'message': f'Bulletin {"créé" if created else "mis à jour"} pour {eleve.nom_complet}',
            'bulletin_id': bulletin.pk
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def prof_principal_bulletins(request):
    """Vue pour que les professeurs principaux gèrent les bulletins de leur classe"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    
    # Vérifier que l'utilisateur est un professeur principal
    if user_type not in ['professeur', 'admin']:
        raise PermissionDenied("Accès réservé aux professeurs principaux et administrateurs.")
    
    # Si c'est un professeur, vérifier qu'il est professeur principal d'au moins une classe
    if user_type == 'professeur':
        classes_prof_principal = Classe.objects.filter(prof_principal=request.user.professeur)
        if not classes_prof_principal.exists():
            raise PermissionDenied("Vous n'êtes pas professeur principal d'aucune classe.")
    else:
        # Si c'est un admin, afficher toutes les classes
        classes_prof_principal = Classe.objects.all()
    
    # Récupérer les bulletins pour les classes du professeur principal
    bulletins = Bulletin.objects.filter(
        classe__in=classes_prof_principal
    ).select_related('eleve', 'classe').order_by('-trimestre', 'eleve__nom')
    
    # Statistiques
    total_bulletins = bulletins.count()
    bulletins_brouillon = bulletins.filter(statut='BROUILLON').count()
    bulletins_valides = bulletins.filter(statut='VALIDE').count()
    
    # Grouper par classe
    bulletins_par_classe = {}
    for bulletin in bulletins:
        classe_nom = bulletin.classe.nom
        if classe_nom not in bulletins_par_classe:
            bulletins_par_classe[classe_nom] = []
        bulletins_par_classe[classe_nom].append(bulletin)
    
    context = {
        'classes_prof_principal': classes_prof_principal,
        'bulletins': bulletins,
        'bulletins_par_classe': bulletins_par_classe,
        'total_bulletins': total_bulletins,
        'bulletins_brouillon': bulletins_brouillon,
        'bulletins_valides': bulletins_valides,
        'user_type': user_type,
    }
    
    return render(request, 'school_management/bulletin/prof_principal_bulletins.html', context)


@login_required
def generer_bulletins_classe(request, classe_id, trimestre):
    """Vue pour générer tous les bulletins d'une classe pour un trimestre"""
    from .permissions import get_user_type
    from django.db import transaction
    from django.contrib import messages
    
    user_type = get_user_type(request.user)
    classe = get_object_or_404(Classe, pk=classe_id)
    
    # Vérifier les permissions
    if user_type == 'admin':
        # L'admin peut générer pour toutes les classes
        pass
    elif user_type == 'professeur':
        # Le professeur ne peut générer que pour ses classes
        if classe.prof_principal != request.user.professeur:
            raise PermissionDenied("Vous n'êtes pas le professeur principal de cette classe.")
    else:
        raise PermissionDenied("Accès non autorisé.")
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                bulletins_crees = 0
                bulletins_mis_a_jour = 0
                erreurs = 0
                
                for eleve in classe.eleves.all():
                    try:
                        # Créer ou mettre à jour le bulletin
                        bulletin, created = Bulletin.objects.get_or_create(
                            eleve=eleve,
                            classe=classe,
                            annee_scolaire='2024-2025',
                            trimestre=trimestre,
                            defaults={
                                'cree_par': request.user,
                                'statut': 'BROUILLON'
                            }
                        )
                        
                        if created:
                            bulletins_crees += 1
                        else:
                            bulletins_mis_a_jour += 1
                            
                        # Générer le contenu détaillé du bulletin
                        generer_contenu_bulletin_detaille(bulletin, eleve, classe, trimestre)
                        
                    except Exception as e:
                        erreurs += 1
                        print(f"Erreur pour l'élève {eleve.nom_complet}: {e}")
                
                messages.success(
                    request, 
                    f"Génération terminée: {bulletins_crees} bulletins créés, "
                    f"{bulletins_mis_a_jour} mis à jour, {erreurs} erreurs."
                )
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération: {e}")
    
    return redirect('school_management:prof_principal_bulletins')


def generer_contenu_bulletin_detaille(bulletin, eleve, classe, trimestre):
    """Génère le contenu détaillé d'un bulletin avec toutes les informations"""
    from django.utils import timezone
    from .models import Note, Evaluation
    
    # Récupérer les notes de l'élève pour le trimestre
    notes = Note.objects.filter(
        eleve=eleve,
        evaluation__date_evaluation__year=timezone.now().year
    ).select_related('evaluation', 'evaluation__matiere')
    
    # Calculer les moyennes par matière
    matieres_notes = {}
    for note in notes:
        matiere = note.evaluation.matiere
        if matiere not in matieres_notes:
            matieres_notes[matiere] = []
        matieres_notes[matiere].append(note.note)
    
    # Calculer les moyennes par matière
    moyennes_par_matiere = {}
    for matiere, notes_list in matieres_notes.items():
        moyennes_par_matiere[matiere] = sum(notes_list) / len(notes_list)
    
    # Calculer la moyenne générale avec coefficients
    if moyennes_par_matiere:
        total_points = 0
        total_coefficients = 0
        for matiere, moyenne in moyennes_par_matiere.items():
            coefficient = matiere.coefficient or 1
            total_points += moyenne * coefficient
            total_coefficients += coefficient
        moyenne_generale = total_points / total_coefficients if total_coefficients > 0 else 0
    else:
        moyenne_generale = 0
    
    # Calculer le rang dans la classe
    eleves_classe = eleve.classe.eleves.all()
    rangs = []
    for e in eleves_classe:
        e_notes = Note.objects.filter(
            eleve=e,
            evaluation__date_evaluation__year=timezone.now().year
        ).select_related('evaluation', 'evaluation__matiere')
        
        e_matieres_notes = {}
        for note in e_notes:
            matiere = note.evaluation.matiere
            if matiere not in e_matieres_notes:
                e_matieres_notes[matiere] = []
            e_matieres_notes[matiere].append(note.note)
        
        e_moyennes = {}
        for matiere, notes_list in e_matieres_notes.items():
            e_moyennes[matiere] = sum(notes_list) / len(notes_list)
        
        if e_moyennes:
            # Calculer la moyenne générale avec coefficients pour le rang
            e_total_points = 0
            e_total_coefficients = 0
            for matiere, moyenne in e_moyennes.items():
                coefficient = matiere.coefficient or 1
                e_total_points += moyenne * coefficient
                e_total_coefficients += coefficient
            e_moyenne_generale = e_total_points / e_total_coefficients if e_total_coefficients > 0 else 0
            rangs.append((e, e_moyenne_generale))
    
    # Trier par moyenne décroissante pour calculer le rang
    rangs.sort(key=lambda x: x[1], reverse=True)
    rang_eleve = 1
    for i, (e, moy) in enumerate(rangs):
        if e == eleve:
            rang_eleve = i + 1
            break
    
    # Calculer la moyenne de la classe
    if rangs:
        moyenne_classe = sum([moy for _, moy in rangs]) / len(rangs)
    else:
        moyenne_classe = 0
    
    # Déterminer la mention
    moyenne_pourcentage = (moyenne_generale / 20) * 100
    
    if moyenne_generale >= 18:
        mention = "EXCELLENT"
    elif moyenne_generale >= 16:
        mention = "TRÈS BIEN"
    elif moyenne_generale >= 14:
        mention = "BIEN"
    elif moyenne_generale >= 12:
        mention = "ASSEZ BIEN"
    elif moyenne_generale >= 10:
        mention = "PASSABLE"
    else:
        mention = "INSUFFISANT"
    
    # Déterminer la décision de passage
    echecs = 0
    for matiere, moyenne in moyennes_par_matiere.items():
        if moyenne < 10:
            echecs += 1
    
    if moyenne_pourcentage < 50:
        decision_passage = "REDOUBLE"
    elif moyenne_pourcentage >= 50 and moyenne_pourcentage <= 100:
        if echecs > 2:
            decision_passage = "SECONDE SESSION"
        else:
            decision_passage = "PASSE EN CLASSE SUPERIEURE"
    else:
        decision_passage = "PASSE EN CLASSE SUPERIEURE"
    
    # Générer l'appréciation générale
    appreciation_generale = generer_appreciation_generale(eleve, moyenne_generale, echecs, len(moyennes_par_matiere))
    
    # Mettre à jour le bulletin avec toutes les informations
    bulletin.moyenne_generale = round(moyenne_generale, 2)
    bulletin.rang = rang_eleve
    bulletin.effectif_classe = len(eleves_classe)
    bulletin.moyenne_classe = round(moyenne_classe, 2)
    bulletin.appreciation_generale = appreciation_generale
    bulletin.save()
    
    return bulletin


def generer_appreciation_generale(eleve, moyenne_generale, echecs, nb_matieres):
    """Génère une appréciation générale personnalisée"""
    prenom = eleve.prenom
    nom = eleve.nom
    
    if moyenne_generale >= 16:
        return f"Excellent travail ! {prenom} {nom} fait preuve d'une grande régularité et d'un excellent niveau dans toutes les matières. Continuez ainsi !"
    elif moyenne_generale >= 14:
        return f"Très bon travail ! {prenom} {nom} progresse bien et montre de bonnes capacités. Quelques efforts supplémentaires permettront d'atteindre l'excellence."
    elif moyenne_generale >= 12:
        return f"Bon travail ! {prenom} {nom} progresse bien dans ses apprentissages. Quelques efforts supplémentaires permettront d'améliorer encore les résultats."
    elif moyenne_generale >= 10:
        if echecs > 0:
            return f"Résultats passables pour {prenom} {nom}. Des efforts importants sont nécessaires dans certaines matières pour améliorer le niveau général."
        else:
            return f"Résultats passables pour {prenom} {nom}. Des efforts supplémentaires permettront d'améliorer les résultats dans toutes les matières."
    else:
        return f"Résultats insuffisants pour {prenom} {nom}. Un travail plus régulier et des efforts importants sont nécessaires pour progresser."


@login_required
def bulletin_detaille_view(request, bulletin_id):
    """Vue pour afficher un bulletin détaillé avec toutes les informations"""
    from .permissions import get_user_type
    from .models import Note
    
    bulletin = get_object_or_404(Bulletin, pk=bulletin_id)
    user_type = get_user_type(request.user)
    
    # Vérifier les permissions
    if user_type == 'admin':
        # L'admin peut voir tous les bulletins
        pass
    elif user_type == 'professeur':
        # Le professeur ne peut voir que les bulletins de ses classes
        if bulletin.classe.prof_principal != request.user.professeur:
            raise PermissionDenied("Vous n'êtes pas le professeur principal de cette classe.")
    elif user_type == 'eleve':
        # L'élève ne peut voir que ses propres bulletins
        if bulletin.eleve != request.user.eleve:
            raise PermissionDenied("Vous ne pouvez voir que vos propres bulletins.")
    elif user_type == 'parent':
        # Le parent ne peut voir que les bulletins de ses enfants
        if not bulletin.eleve.parents.filter(user=request.user).exists():
            raise PermissionDenied("Vous ne pouvez voir que les bulletins de vos enfants.")
    else:
        raise PermissionDenied("Accès non autorisé.")
    
    # Récupérer les notes détaillées
    notes = Note.objects.filter(
        eleve=bulletin.eleve,
        evaluation__date_evaluation__year=timezone.now().year
    ).select_related('evaluation', 'evaluation__matiere').order_by('evaluation__matiere__nom', 'evaluation__date_evaluation')
    
    # Organiser les notes par matière
    notes_par_matiere = {}
    for note in notes:
        matiere = note.evaluation.matiere
        if matiere not in notes_par_matiere:
            notes_par_matiere[matiere] = []
        notes_par_matiere[matiere].append(note)
    
    # Calculer les moyennes par matière
    moyennes_par_matiere = {}
    for matiere, notes_list in notes_par_matiere.items():
        moyennes_par_matiere[matiere] = sum([n.note for n in notes_list]) / len(notes_list)
    
    # Calculer les statistiques
    moyenne_generale = bulletin.moyenne_generale or 0
    moyenne_pourcentage = (moyenne_generale / 20) * 100
    
    # Compter les échecs
    echecs = 0
    for matiere, moyenne in moyennes_par_matiere.items():
        if moyenne < 10:
            echecs += 1
    
    # Déterminer la mention
    if moyenne_generale >= 18:
        mention = "EXCELLENT"
        couleur_mention = "success"
    elif moyenne_generale >= 16:
        mention = "TRÈS BIEN"
        couleur_mention = "primary"
    elif moyenne_generale >= 14:
        mention = "BIEN"
        couleur_mention = "info"
    elif moyenne_generale >= 12:
        mention = "ASSEZ BIEN"
        couleur_mention = "warning"
    elif moyenne_generale >= 10:
        mention = "PASSABLE"
        couleur_mention = "secondary"
    else:
        mention = "INSUFFISANT"
        couleur_mention = "danger"
    
    # Déterminer la décision de passage
    if moyenne_pourcentage < 50:
        decision_passage = "REDOUBLE"
        couleur_decision = "danger"
    elif moyenne_pourcentage >= 50 and moyenne_pourcentage <= 100:
        if echecs > 2:
            decision_passage = "SECONDE SESSION"
            couleur_decision = "warning"
        else:
            decision_passage = "PASSE EN CLASSE SUPERIEURE"
            couleur_decision = "success"
    else:
        decision_passage = "PASSE EN CLASSE SUPERIEURE"
        couleur_decision = "success"
    
    context = {
        'bulletin': bulletin,
        'notes_par_matiere': notes_par_matiere,
        'moyennes_par_matiere': moyennes_par_matiere,
        'moyenne_generale': moyenne_generale,
        'moyenne_pourcentage': round(moyenne_pourcentage, 1),
        'mention': mention,
        'couleur_mention': couleur_mention,
        'decision_passage': decision_passage,
        'couleur_decision': couleur_decision,
        'echecs': echecs,
        'nb_matieres': len(moyennes_par_matiere),
        'user_type': user_type,
    }
    
    return render(request, 'school_management/bulletin/bulletin_detaille.html', context)


@login_required
def publier_bulletin(request, bulletin_id):
    """Vue pour publier un bulletin (le rendre visible aux parents et élèves)"""
    from .permissions import get_user_type
    
    bulletin = get_object_or_404(Bulletin, pk=bulletin_id)
    user_type = get_user_type(request.user)
    
    # Vérifier les permissions
    if user_type == 'admin':
        # L'admin peut publier tous les bulletins
        pass
    elif user_type == 'professeur':
        # Le professeur ne peut publier que les bulletins de ses classes
        if bulletin.classe.prof_principal != request.user.professeur:
            raise PermissionDenied("Vous n'êtes pas le professeur principal de cette classe.")
    else:
        raise PermissionDenied("Seuls les administrateurs et professeurs principaux peuvent publier les bulletins.")
    
    # Vérifier que le bulletin est prêt à être publié
    if bulletin.statut not in ['BROUILLON', 'EN_ATTENTE']:
        messages.warning(request, f"Ce bulletin est déjà {bulletin.get_statut_display().lower()}.")
        return redirect('school_management:prof_principal_bulletins')
    
    # Publier le bulletin
    bulletin.statut = 'PUBLIE'
    bulletin.date_publication = timezone.now()
    bulletin.save()
    
    messages.success(request, f"Le bulletin de {bulletin.eleve.prenom} {bulletin.eleve.nom} a été publié avec succès. Il est maintenant visible par les parents et l'élève.")
    
    return redirect('school_management:prof_principal_bulletins')


@login_required
def publier_bulletins_classe(request, classe_id, trimestre):
    """Vue pour publier tous les bulletins d'une classe pour un trimestre"""
    from .permissions import get_user_type
    
    classe = get_object_or_404(Classe, pk=classe_id)
    user_type = get_user_type(request.user)
    
    # Vérifier les permissions
    if user_type == 'admin':
        # L'admin peut publier tous les bulletins
        pass
    elif user_type == 'professeur':
        # Le professeur ne peut publier que les bulletins de ses classes
        if classe.prof_principal != request.user.professeur:
            raise PermissionDenied("Vous n'êtes pas le professeur principal de cette classe.")
    else:
        raise PermissionDenied("Seuls les administrateurs et professeurs principaux peuvent publier les bulletins.")
    
    # Récupérer tous les bulletins de la classe pour le trimestre
    bulletins = Bulletin.objects.filter(
        classe=classe,
        trimestre=trimestre,
        statut__in=['BROUILLON', 'EN_ATTENTE']
    )
    
    if not bulletins.exists():
        messages.warning(request, f"Aucun bulletin à publier pour la {classe.nom} au trimestre {trimestre}.")
        return redirect('school_management:prof_principal_bulletins')
    
    # Publier tous les bulletins
    bulletins_publies = 0
    for bulletin in bulletins:
        bulletin.statut = 'PUBLIE'
        bulletin.date_publication = timezone.now()
        bulletin.save()
        bulletins_publies += 1
    
    messages.success(request, f"{bulletins_publies} bulletin(s) de la {classe.nom} pour le trimestre {trimestre} ont été publiés avec succès.")
    
    return redirect('school_management:prof_principal_bulletins')


@login_required
def mes_bulletins(request):
    """Vue pour que les parents et élèves consultent leurs bulletins publiés"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    bulletins = []
    
    if user_type == 'eleve':
        # L'élève peut voir ses propres bulletins publiés
        bulletins = Bulletin.objects.filter(
            eleve=request.user.eleve,
            statut='PUBLIE'
        ).select_related('classe').order_by('-trimestre', '-date_creation')
        
    elif user_type == 'parent':
        # Le parent peut voir les bulletins publiés de ses enfants
        enfants = request.user.parent.eleves.all()
        bulletins = Bulletin.objects.filter(
            eleve__in=enfants,
            statut='PUBLIE'
        ).select_related('eleve', 'classe').order_by('eleve__nom', '-trimestre', '-date_creation')
        
    elif user_type == 'admin':
        # L'admin peut voir tous les bulletins publiés
        bulletins = Bulletin.objects.filter(
            statut='PUBLIE'
        ).select_related('eleve', 'classe').order_by('classe__nom', 'eleve__nom', '-trimestre', '-date_creation')
        
    else:
        raise PermissionDenied("Accès non autorisé.")
    
    # Organiser les bulletins par élève et trimestre
    bulletins_par_eleve = {}
    for bulletin in bulletins:
        if user_type == 'parent':
            eleve_key = f"{bulletin.eleve.prenom} {bulletin.eleve.nom}"
        else:
            eleve_key = "Mes bulletins"
            
        if eleve_key not in bulletins_par_eleve:
            bulletins_par_eleve[eleve_key] = []
        bulletins_par_eleve[eleve_key].append(bulletin)
    
    context = {
        'bulletins_par_eleve': bulletins_par_eleve,
        'user_type': user_type,
    }
    
    return render(request, 'school_management/bulletin/mes_bulletins.html', context)


