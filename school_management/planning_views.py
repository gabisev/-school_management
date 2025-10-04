from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Salle, Creneau, EmploiDuTemps, EvenementCalendrier, ReservationSalle,
    Classe, Matiere, Professeur, Eleve
)
from .forms import (
    SalleForm, CreneauForm, EmploiDuTempsForm, EvenementCalendrierForm,
    ReservationSalleForm, ValidationReservationForm
)
from .permissions import get_user_type


# =============== VUE PRINCIPALE DU PLANNING ===============

@login_required
def planning_dashboard(request):
    """Vue principale du planning - tableau de bord"""
    user_type = get_user_type(request.user)
    
    # Statistiques générales
    total_salles = Salle.objects.filter(active=True).count()
    total_creneaux = Creneau.objects.count()
    total_emplois = EmploiDuTemps.objects.filter(actif=True).count()
    total_evenements = EvenementCalendrier.objects.filter(actif=True).count()
    total_reservations = ReservationSalle.objects.filter(statut='CONFIRME').count()
    
    # Événements récents
    evenements_recents = EvenementCalendrier.objects.filter(
        actif=True,
        date_debut__gte=timezone.now().date()
    ).order_by('date_debut')[:5]
    
    # Réservations en attente (pour les admins)
    reservations_en_attente = []
    if user_type == 'admin':
        reservations_en_attente = ReservationSalle.objects.filter(
            statut='EN_ATTENTE'
        ).order_by('date_debut')[:5]
    
    # Emplois du temps de l'utilisateur (si élève ou professeur)
    emplois_utilisateur = []
    if user_type == 'eleve' and hasattr(request.user, 'eleve'):
        emplois_utilisateur = EmploiDuTemps.objects.filter(
            classe=request.user.eleve.classe,
            actif=True
        ).select_related('matiere', 'professeur', 'salle', 'creneau').order_by('creneau__jour', 'creneau__heure_debut')[:5]
    elif user_type == 'professeur' and hasattr(request.user, 'professeur'):
        emplois_utilisateur = EmploiDuTemps.objects.filter(
            professeur=request.user.professeur,
            actif=True
        ).select_related('classe', 'matiere', 'salle', 'creneau').order_by('creneau__jour', 'creneau__heure_debut')[:5]
    
    context = {
        'user_type': user_type,
        'total_salles': total_salles,
        'total_creneaux': total_creneaux,
        'total_emplois': total_emplois,
        'total_evenements': total_evenements,
        'total_reservations': total_reservations,
        'evenements_recents': evenements_recents,
        'reservations_en_attente': reservations_en_attente,
        'emplois_utilisateur': emplois_utilisateur,
    }
    
    return render(request, 'school_management/planning/planning_dashboard.html', context)


# =============== VUES POUR LES SALLES ===============

class SalleListView(LoginRequiredMixin, ListView):
    """Vue pour lister les salles"""
    model = Salle
    template_name = 'school_management/planning/salle_list.html'
    context_object_name = 'salles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Salle.objects.all()
        type_salle = self.request.GET.get('type_salle')
        if type_salle:
            queryset = queryset.filter(type_salle=type_salle)
        return queryset.order_by('numero')


class SalleDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'une salle"""
    model = Salle
    template_name = 'school_management/planning/salle_detail.html'
    context_object_name = 'salle'


class SalleCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle salle"""
    model = Salle
    form_class = SalleForm
    template_name = 'school_management/planning/salle_form.html'
    success_url = reverse_lazy('school_management:salle_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Accès réservé aux administrateurs et professeurs.")
        return super().dispatch(request, *args, **kwargs)


class SalleUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une salle"""
    model = Salle
    form_class = SalleForm
    template_name = 'school_management/planning/salle_form.html'
    success_url = reverse_lazy('school_management:salle_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Accès réservé aux administrateurs et professeurs.")
        return super().dispatch(request, *args, **kwargs)


class SalleDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une salle"""
    model = Salle
    template_name = 'school_management/planning/salle_confirm_delete.html'
    success_url = reverse_lazy('school_management:salle_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


# =============== VUES POUR LES CRÉNEAUX ===============

class CreneauListView(LoginRequiredMixin, ListView):
    """Vue pour lister les créneaux"""
    model = Creneau
    template_name = 'school_management/planning/creneau_list.html'
    context_object_name = 'creneaux'
    
    def get_queryset(self):
        return Creneau.objects.all().order_by('jour', 'heure_debut')


class CreneauCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouveau créneau"""
    model = Creneau
    form_class = CreneauForm
    template_name = 'school_management/planning/creneau_form.html'
    success_url = reverse_lazy('school_management:creneau_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


class CreneauUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un créneau"""
    model = Creneau
    form_class = CreneauForm
    template_name = 'school_management/planning/creneau_form.html'
    success_url = reverse_lazy('school_management:creneau_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


class CreneauDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un créneau"""
    model = Creneau
    template_name = 'school_management/planning/creneau_confirm_delete.html'
    success_url = reverse_lazy('school_management:creneau_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


# =============== VUES POUR L'EMPLOI DU TEMPS ===============

class EmploiDuTempsListView(LoginRequiredMixin, ListView):
    """Vue pour lister les emplois du temps"""
    model = EmploiDuTemps
    template_name = 'school_management/planning/emploi_list.html'
    context_object_name = 'emplois'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EmploiDuTemps.objects.select_related(
            'classe', 'matiere', 'professeur', 'salle', 'creneau'
        ).filter(actif=True)
        
        # Filtres
        classe_id = self.request.GET.get('classe')
        professeur_id = self.request.GET.get('professeur')
        annee_scolaire = self.request.GET.get('annee_scolaire', '2024-2025')
        semestre = self.request.GET.get('semestre')
        
        if classe_id:
            queryset = queryset.filter(classe_id=classe_id)
        if professeur_id:
            queryset = queryset.filter(professeur_id=professeur_id)
        if annee_scolaire:
            queryset = queryset.filter(annee_scolaire=annee_scolaire)
        if semestre:
            queryset = queryset.filter(semestre=semestre)
        
        return queryset.order_by('classe', 'creneau__jour', 'creneau__heure_debut')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = Classe.objects.all().order_by('niveau', 'nom')
        context['professeurs'] = Professeur.objects.all().order_by('user__last_name')
        return context


class EmploiDuTempsDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un emploi du temps"""
    model = EmploiDuTemps
    template_name = 'school_management/planning/emploi_detail.html'
    context_object_name = 'emploi'


class EmploiDuTempsCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouvel emploi du temps"""
    model = EmploiDuTemps
    form_class = EmploiDuTempsForm
    template_name = 'school_management/planning/emploi_form.html'
    success_url = reverse_lazy('school_management:emploi_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Accès réservé aux administrateurs et professeurs.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        emploi = form.save(commit=False)
        
        # Valider le modèle
        try:
            emploi.clean()
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        
        # Vérifier les conflits
        if emploi.a_des_conflits():
            messages.warning(
                self.request,
                "Attention : Des conflits ont été détectés dans l'emploi du temps."
            )
        
        return super().form_valid(form)


class EmploiDuTempsUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un emploi du temps"""
    model = EmploiDuTemps
    form_class = EmploiDuTempsForm
    template_name = 'school_management/planning/emploi_form.html'
    success_url = reverse_lazy('school_management:emploi_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Accès réservé aux administrateurs et professeurs.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        emploi = form.save(commit=False)
        
        # Valider le modèle
        try:
            emploi.clean()
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        
        # Vérifier les conflits
        if emploi.a_des_conflits():
            messages.warning(
                self.request,
                "Attention : Des conflits ont été détectés dans l'emploi du temps."
            )
        
        return super().form_valid(form)


class EmploiDuTempsDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un emploi du temps"""
    model = EmploiDuTemps
    template_name = 'school_management/planning/emploi_confirm_delete.html'
    success_url = reverse_lazy('school_management:emploi_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def emploi_du_temps_classe(request, classe_id):
    """Vue pour afficher l'emploi du temps d'une classe"""
    classe = get_object_or_404(Classe, pk=classe_id)
    annee_scolaire = request.GET.get('annee_scolaire', '2024-2025')
    semestre = request.GET.get('semestre', 1)
    
    emplois = EmploiDuTemps.objects.filter(
        classe=classe,
        annee_scolaire=annee_scolaire,
        semestre=semestre,
        actif=True
    ).select_related('matiere', 'professeur', 'salle', 'creneau').order_by(
        'creneau__jour', 'creneau__heure_debut'
    )
    
    # Organiser par jour et créneau
    emplois_par_jour = {}
    jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
    
    for jour in jours:
        emplois_par_jour[jour] = emplois.filter(creneau__jour=jour)
    
    context = {
        'classe': classe,
        'emplois_par_jour': emplois_par_jour,
        'annee_scolaire': annee_scolaire,
        'semestre': semestre,
    }
    
    return render(request, 'school_management/planning/emploi_classe.html', context)


@login_required
def emploi_du_temps_professeur(request, professeur_id):
    """Vue pour afficher l'emploi du temps d'un professeur"""
    professeur = get_object_or_404(Professeur, pk=professeur_id)
    annee_scolaire = request.GET.get('annee_scolaire', '2024-2025')
    semestre = request.GET.get('semestre', 1)
    
    emplois = EmploiDuTemps.objects.filter(
        professeur=professeur,
        annee_scolaire=annee_scolaire,
        semestre=semestre,
        actif=True
    ).select_related('classe', 'matiere', 'salle', 'creneau').order_by(
        'creneau__jour', 'creneau__heure_debut'
    )
    
    # Organiser par jour et créneau
    emplois_par_jour = {}
    jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
    
    for jour in jours:
        emplois_par_jour[jour] = emplois.filter(creneau__jour=jour)
    
    context = {
        'professeur': professeur,
        'emplois_par_jour': emplois_par_jour,
        'annee_scolaire': annee_scolaire,
        'semestre': semestre,
    }
    
    return render(request, 'school_management/planning/emploi_professeur.html', context)


# =============== VUES POUR LE CALENDRIER ===============

class EvenementCalendrierListView(LoginRequiredMixin, ListView):
    """Vue pour lister les événements du calendrier"""
    model = EvenementCalendrier
    template_name = 'school_management/planning/evenement_list.html'
    context_object_name = 'evenements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EvenementCalendrier.objects.filter(actif=True)
        
        # Filtres
        type_evenement = self.request.GET.get('type_evenement')
        annee_scolaire = self.request.GET.get('annee_scolaire', '2024-2025')
        
        if type_evenement:
            queryset = queryset.filter(type_evenement=type_evenement)
        if annee_scolaire:
            queryset = queryset.filter(annee_scolaire=annee_scolaire)
        
        return queryset.order_by('-date_debut')


class EvenementCalendrierDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un événement"""
    model = EvenementCalendrier
    template_name = 'school_management/planning/evenement_detail.html'
    context_object_name = 'evenement'


class EvenementCalendrierCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouvel événement"""
    model = EvenementCalendrier
    form_class = EvenementCalendrierForm
    template_name = 'school_management/planning/evenement_form.html'
    success_url = reverse_lazy('school_management:evenement_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Accès réservé aux administrateurs et professeurs.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        evenement = form.save(commit=False)
        evenement.organisateur = self.request.user
        return super().form_valid(form)


class EvenementCalendrierUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un événement"""
    model = EvenementCalendrier
    form_class = EvenementCalendrierForm
    template_name = 'school_management/planning/evenement_form.html'
    success_url = reverse_lazy('school_management:evenement_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Accès réservé aux administrateurs et professeurs.")
        return super().dispatch(request, *args, **kwargs)


class EvenementCalendrierDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un événement"""
    model = EvenementCalendrier
    template_name = 'school_management/planning/evenement_confirm_delete.html'
    success_url = reverse_lazy('school_management:evenement_list')
    
    def dispatch(self, request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def calendrier_view(request):
    """Vue pour afficher le calendrier complet"""
    annee_scolaire = request.GET.get('annee_scolaire', '2024-2025')
    mois = request.GET.get('mois', timezone.now().month)
    annee = request.GET.get('annee', timezone.now().year)
    
    # Récupérer les événements du mois
    debut_mois = datetime(int(annee), int(mois), 1)
    if int(mois) == 12:
        fin_mois = datetime(int(annee) + 1, 1, 1) - timedelta(days=1)
    else:
        fin_mois = datetime(int(annee), int(mois) + 1, 1) - timedelta(days=1)
    
    evenements = EvenementCalendrier.objects.filter(
        annee_scolaire=annee_scolaire,
        actif=True,
        date_debut__lte=fin_mois,
        date_fin__gte=debut_mois
    ).order_by('date_debut')
    
    context = {
        'evenements': evenements,
        'annee_scolaire': annee_scolaire,
        'mois': int(mois),
        'annee': int(annee),
        'debut_mois': debut_mois,
        'fin_mois': fin_mois,
    }
    
    return render(request, 'school_management/planning/calendrier.html', context)


# =============== VUES POUR LES RÉSERVATIONS ===============

class ReservationSalleListView(LoginRequiredMixin, ListView):
    """Vue pour lister les réservations de salles"""
    model = ReservationSalle
    template_name = 'school_management/planning/reservation_list.html'
    context_object_name = 'reservations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ReservationSalle.objects.select_related('salle', 'utilisateur')
        
        # Filtres
        statut = self.request.GET.get('statut')
        salle_id = self.request.GET.get('salle')
        
        if statut:
            queryset = queryset.filter(statut=statut)
        if salle_id:
            queryset = queryset.filter(salle_id=salle_id)
        
        return queryset.order_by('-date_debut')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['salles'] = Salle.objects.filter(active=True).order_by('numero')
        return context


class ReservationSalleDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'une réservation"""
    model = ReservationSalle
    template_name = 'school_management/planning/reservation_detail.html'
    context_object_name = 'reservation'


class ReservationSalleCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle réservation"""
    model = ReservationSalle
    form_class = ReservationSalleForm
    template_name = 'school_management/planning/reservation_form.html'
    success_url = reverse_lazy('school_management:reservation_list')
    
    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.utilisateur = self.request.user
        return super().form_valid(form)


class ReservationSalleUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une réservation"""
    model = ReservationSalle
    form_class = ReservationSalleForm
    template_name = 'school_management/planning/reservation_form.html'
    success_url = reverse_lazy('school_management:reservation_list')
    
    def dispatch(self, request, *args, **kwargs):
        reservation = self.get_object()
        if not reservation.peut_etre_modifiee_par(request.user):
            raise PermissionDenied("Vous ne pouvez pas modifier cette réservation.")
        return super().dispatch(request, *args, **kwargs)


class ReservationSalleDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une réservation"""
    model = ReservationSalle
    template_name = 'school_management/planning/reservation_confirm_delete.html'
    success_url = reverse_lazy('school_management:reservation_list')
    
    def dispatch(self, request, *args, **kwargs):
        reservation = self.get_object()
        if not reservation.peut_etre_modifiee_par(request.user):
            raise PermissionDenied("Vous ne pouvez pas supprimer cette réservation.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def valider_reservation(request, pk):
    """Vue pour valider ou refuser une réservation"""
    reservation = get_object_or_404(ReservationSalle, pk=pk)
    
    user_type = get_user_type(request.user)
    if user_type not in ['admin', 'professeur']:
        raise PermissionDenied("Accès réservé aux administrateurs et professeurs.")
    
    if request.method == 'POST':
        form = ValidationReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.valide_par = request.user
            reservation.date_validation = timezone.now()
            reservation.save()
            
            messages.success(request, f"Réservation {reservation.get_statut_display().lower()} avec succès.")
            return redirect('school_management:reservation_detail', pk=pk)
    else:
        form = ValidationReservationForm(instance=reservation)
    
    context = {
        'reservation': reservation,
        'form': form,
    }
    
    return render(request, 'school_management/planning/validation_reservation.html', context)


# =============== VUES AJAX ===============

@login_required
def get_salles_disponibles(request):
    """Vue AJAX pour récupérer les salles disponibles à une heure donnée"""
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if not date_debut or not date_fin:
        return JsonResponse({'error': 'Dates manquantes'}, status=400)
    
    try:
        date_debut = datetime.fromisoformat(date_debut.replace('Z', '+00:00'))
        date_fin = datetime.fromisoformat(date_fin.replace('Z', '+00:00'))
    except ValueError:
        return JsonResponse({'error': 'Format de date invalide'}, status=400)
    
    # Salles occupées pendant cette période
    salles_occupees = ReservationSalle.objects.filter(
        statut='CONFIRME',
        date_debut__lt=date_fin,
        date_fin__gt=date_debut
    ).values_list('salle_id', flat=True)
    
    # Salles disponibles
    salles_disponibles = Salle.objects.filter(
        active=True
    ).exclude(id__in=salles_occupees).values('id', 'nom', 'numero', 'capacite')
    
    return JsonResponse({
        'salles': list(salles_disponibles)
    })


@login_required
def get_conflits_emploi(request):
    """Vue AJAX pour vérifier les conflits dans l'emploi du temps"""
    classe_id = request.GET.get('classe_id')
    professeur_id = request.GET.get('professeur_id')
    salle_id = request.GET.get('salle_id')
    creneau_id = request.GET.get('creneau_id')
    annee_scolaire = request.GET.get('annee_scolaire', '2024-2025')
    semestre = request.GET.get('semestre', 1)
    
    conflits = []
    
    # Conflit professeur
    if professeur_id and creneau_id:
        conflit_prof = EmploiDuTemps.objects.filter(
            professeur_id=professeur_id,
            creneau_id=creneau_id,
            annee_scolaire=annee_scolaire,
            semestre=semestre,
            actif=True
        ).first()
        if conflit_prof:
            conflits.append(f"Le professeur a déjà un cours à ce créneau ({conflit_prof.classe})")
    
    # Conflit salle
    if salle_id and creneau_id:
        conflit_salle = EmploiDuTemps.objects.filter(
            salle_id=salle_id,
            creneau_id=creneau_id,
            annee_scolaire=annee_scolaire,
            semestre=semestre,
            actif=True
        ).first()
        if conflit_salle:
            conflits.append(f"La salle est déjà occupée à ce créneau ({conflit_salle.classe})")
    
    # Conflit classe
    if classe_id and creneau_id:
        conflit_classe = EmploiDuTemps.objects.filter(
            classe_id=classe_id,
            creneau_id=creneau_id,
            annee_scolaire=annee_scolaire,
            semestre=semestre,
            actif=True
        ).first()
        if conflit_classe:
            conflits.append(f"La classe a déjà un cours à ce créneau ({conflit_classe.matiere})")
    
    return JsonResponse({
        'conflits': conflits,
        'has_conflits': len(conflits) > 0
    })


@login_required
def emploi_du_temps_eleve(request):
    """Vue pour l'emploi du temps d'un élève"""
    user_type = get_user_type(request.user)
    
    if user_type != 'eleve':
        raise PermissionDenied("Accès réservé aux élèves.")
    
    try:
        eleve = request.user.eleve
    except:
        raise PermissionDenied("Profil élève non trouvé.")
    
    # Récupérer l'emploi du temps de la classe de l'élève
    emplois = EmploiDuTemps.objects.filter(
        classe=eleve.classe,
        actif=True
    ).select_related('matiere', 'professeur', 'salle', 'creneau').order_by('creneau__jour', 'creneau__heure_debut')
    
    # Organiser par jour et créneau
    emploi_par_jour = {}
    jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
    
    # Récupérer tous les créneaux pour construire la grille
    creneaux = Creneau.objects.all().order_by('heure_debut')
    
    for jour in jours:
        emploi_par_jour[jour] = {}
        for creneau in creneaux:
            emploi_par_jour[jour][creneau.id] = None
    
    # Remplir avec les emplois existants
    for emploi in emplois:
        if emploi.creneau.jour in emploi_par_jour:
            emploi_par_jour[emploi.creneau.jour][emploi.creneau.id] = emploi
    
    # Récupérer les événements de la classe
    evenements = EvenementCalendrier.objects.filter(
        Q(classes_concernees=eleve.classe) | Q(classes_concernees__isnull=True),
        actif=True,
        date_debut__gte=timezone.now().date()
    ).order_by('date_debut')[:10]
    
    context = {
        'eleve': eleve,
        'emploi_par_jour': emploi_par_jour,
        'jours': jours,
        'creneaux': creneaux,
        'evenements': evenements,
        'classe': eleve.classe,
    }
    
    return render(request, 'school_management/planning/emploi_eleve.html', context)
