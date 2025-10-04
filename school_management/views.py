from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from .models import (
    Classe, Matiere, Professeur, Eleve,
    Evaluation, Note, Absence, AnneeScolaire, Parent, Communication, Conversation, Message
)
from .forms import NoteFormSet, ProfesseurForm, ParentForm, CommunicationForm, CustomLoginForm, UserProfileForm, PasswordChangeForm


@login_required
def dashboard(request):
    """Vue du tableau de bord principal"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    
    # Redirection selon le type d'utilisateur
    if user_type == 'eleve':
        return redirect('school_management:eleve_dashboard')
    elif user_type == 'professeur':
        return redirect('school_management:professeur_dashboard')
    elif user_type == 'parent':
        return redirect('school_management:parent_dashboard')
    elif user_type == 'admin':
        return redirect('school_management:admin_dashboard')
    
    # Dashboard par défaut (fallback)
    context = {
        'total_eleves': Eleve.objects.filter(statut=True).count(),
        'total_professeurs': Professeur.objects.count(),
        'total_classes': Classe.objects.count(),
        'total_matieres': Matiere.objects.count(),
        'absences_non_justifiees': Absence.objects.filter(justifiee=False).count(),
        'evaluations_recentes': Evaluation.objects.order_by('-date_evaluation')[:5],
        'classes_list': Classe.objects.annotate(nb_eleves=Count('eleves')),
    }
    return render(request, 'school_management/dashboard.html', context)


# =============== VUES POUR LES ÉLÈVES ===============

class EleveListView(LoginRequiredMixin, ListView):
    model = Eleve
    template_name = 'school_management/eleve/list.html'
    context_object_name = 'eleves'
    paginate_by = 20
    
    def get_queryset(self):
        from .permissions import get_user_type
        
        queryset = Eleve.objects.filter(statut=True).select_related('classe')
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne voit que ses propres informations
            queryset = queryset.filter(pk=self.request.user.eleve.pk)
        elif user_type == 'professeur':
            # Un professeur ne voit que les élèves de ses classes
            queryset = queryset.filter(classe__in=self.request.user.professeur.classes.all())
        
        # Appliquer les filtres de recherche seulement pour les professeurs et admins
        if user_type in ['professeur', 'admin']:
            search = self.request.GET.get('search')
            classe_filter = self.request.GET.get('classe')
            
            if search:
                queryset = queryset.filter(
                    Q(nom__icontains=search) | 
                    Q(prenom__icontains=search) |
                    Q(numero_etudiant__icontains=search)
                )
            
            if classe_filter:
                queryset = queryset.filter(classe_id=classe_filter)
            
        return queryset.order_by('nom', 'prenom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = Classe.objects.all()
        return context


class EleveDetailView(LoginRequiredMixin, DetailView):
    model = Eleve
    template_name = 'school_management/eleve/detail.html'
    context_object_name = 'eleve'
    
    def get_object(self, queryset=None):
        from .permissions import check_eleve_access
        
        obj = super().get_object(queryset)
        check_eleve_access(self.request.user, obj)
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        eleve = self.get_object()
        context['notes'] = Note.objects.filter(eleve=eleve).select_related('evaluation', 'evaluation__matiere')
        context['absences'] = Absence.objects.filter(eleve=eleve).order_by('-date_debut')[:10]
        return context


class EleveCreateView(LoginRequiredMixin, CreateView):
    model = Eleve
    template_name = 'school_management/eleve/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent créer des élèves")
        
        return super().dispatch(request, *args, **kwargs)
    fields = [
        'nom', 'prenom', 'date_naissance', 'lieu_naissance', 'sexe', 'nationalite',
        'numero_etudiant', 'classe', 'adresse', 'telephone', 'email',
        'nom_pere', 'telephone_pere', 'profession_pere',
        'nom_mere', 'telephone_mere', 'profession_mere', 'photo'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, 'Élève ajouté avec succès!')
        return super().form_valid(form)


class EleveUpdateView(LoginRequiredMixin, UpdateView):
    model = Eleve
    template_name = 'school_management/eleve/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent modifier les élèves")
        
        return super().dispatch(request, *args, **kwargs)
    fields = [
        'nom', 'prenom', 'date_naissance', 'lieu_naissance', 'sexe', 'nationalite',
        'numero_etudiant', 'classe', 'adresse', 'telephone', 'email',
        'nom_pere', 'telephone_pere', 'profession_pere',
        'nom_mere', 'telephone_mere', 'profession_mere', 'photo', 'statut'
    ]
    
    def form_valid(self, form):
        messages.success(self.request, 'Informations de l\'élève modifiées avec succès!')
        return super().form_valid(form)


class EleveDeleteView(LoginRequiredMixin, DeleteView):
    model = Eleve
    template_name = 'school_management/eleve/confirm_delete.html'
    success_url = reverse_lazy('school_management:eleve_list')
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer les élèves")
        
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Élève supprimé avec succès!')
        return super().delete(request, *args, **kwargs)


# =============== VUES POUR LES PROFESSEURS ===============

class ProfesseurListView(LoginRequiredMixin, ListView):
    model = Professeur
    template_name = 'school_management/professeur/list.html'
    context_object_name = 'professeurs'
    paginate_by = 20
    
    def get_queryset(self):
        from .permissions import get_user_type
        
        queryset = Professeur.objects.all()
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne peut voir que les professeurs de sa classe
            return queryset.filter(classes=self.request.user.eleve.classe)
        elif user_type == 'professeur':
            # Un professeur ne voit que lui-même
            return queryset.filter(pk=self.request.user.professeur.pk)
        
        return queryset


class ProfesseurDetailView(LoginRequiredMixin, DetailView):
    model = Professeur
    template_name = 'school_management/professeur/detail.html'
    context_object_name = 'professeur'


class ProfesseurCreateView(LoginRequiredMixin, CreateView):
    model = Professeur
    form_class = ProfesseurForm
    template_name = 'school_management/professeur/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent créer des professeurs")
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Professeur ajouté avec succès!')
        return super().form_valid(form)


class ProfesseurUpdateView(LoginRequiredMixin, UpdateView):
    model = Professeur
    form_class = ProfesseurForm
    template_name = 'school_management/professeur/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Informations du professeur modifiées avec succès!')
        return super().form_valid(form)


class ProfesseurDeleteView(LoginRequiredMixin, DeleteView):
    model = Professeur
    template_name = 'school_management/professeur/confirm_delete.html'
    success_url = reverse_lazy('school_management:professeur_list')


# =============== VUES POUR LES CLASSES ===============

class ClasseListView(LoginRequiredMixin, ListView):
    model = Classe
    template_name = 'school_management/classe/list.html'
    context_object_name = 'classes'
    
    def get_queryset(self):
        from .permissions import get_user_type
        queryset = Classe.objects.annotate(nb_eleves=Count('eleves'))
        user_type = get_user_type(self.request.user)
        
        if user_type == 'professeur':
            # Un professeur ne voit que ses classes assignées
            queryset = queryset.filter(professeurs=self.request.user.professeur)
        
        return queryset


class ClasseDetailView(LoginRequiredMixin, DetailView):
    model = Classe
    template_name = 'school_management/classe/detail.html'
    context_object_name = 'classe'
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'professeur':
            # Un professeur ne peut accéder qu'aux détails de ses classes
            if obj not in self.request.user.professeur.classes.all():
                raise PermissionDenied("Vous ne pouvez accéder qu'aux détails de vos classes.")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classe = self.get_object()
        context['eleves'] = classe.eleves.filter(statut=True).order_by('nom', 'prenom')
        context['professeurs'] = classe.professeurs.all()
        return context


class ClasseCreateView(LoginRequiredMixin, CreateView):
    model = Classe
    template_name = 'school_management/classe/form.html'
    fields = ['nom', 'niveau', 'annee_scolaire', 'effectif_max']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent créer des classes")
        
        return super().dispatch(request, *args, **kwargs)


class ClasseUpdateView(LoginRequiredMixin, UpdateView):
    model = Classe
    template_name = 'school_management/classe/form.html'
    fields = ['nom', 'niveau', 'annee_scolaire', 'effectif_max']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent modifier des classes")
        
        return super().dispatch(request, *args, **kwargs)


class ClasseDeleteView(LoginRequiredMixin, DeleteView):
    model = Classe
    template_name = 'school_management/classe/confirm_delete.html'
    success_url = reverse_lazy('school_management:classe_list')
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des classes")
        
        return super().dispatch(request, *args, **kwargs)


# =============== VUES POUR LES MATIÈRES ===============

class MatiereListView(LoginRequiredMixin, ListView):
    model = Matiere
    template_name = 'school_management/matiere/list.html'
    context_object_name = 'matieres'


class MatiereDetailView(LoginRequiredMixin, DetailView):
    model = Matiere
    template_name = 'school_management/matiere/detail.html'
    context_object_name = 'matiere'


class MatiereCreateView(LoginRequiredMixin, CreateView):
    model = Matiere
    template_name = 'school_management/matiere/form.html'
    fields = ['nom', 'code', 'coefficient', 'description']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent créer des matières")
        
        return super().dispatch(request, *args, **kwargs)


class MatiereUpdateView(LoginRequiredMixin, UpdateView):
    model = Matiere
    template_name = 'school_management/matiere/form.html'
    fields = ['nom', 'code', 'coefficient', 'description']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent modifier des matières")
        
        return super().dispatch(request, *args, **kwargs)


class MatiereDeleteView(LoginRequiredMixin, DeleteView):
    model = Matiere
    template_name = 'school_management/matiere/confirm_delete.html'
    success_url = reverse_lazy('school_management:matiere_list')
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des matières")
        
        return super().dispatch(request, *args, **kwargs)


# =============== VUES POUR LES ÉVALUATIONS ===============

class EvaluationListView(LoginRequiredMixin, ListView):
    model = Evaluation
    template_name = 'school_management/evaluation/list.html'
    context_object_name = 'evaluations'
    paginate_by = 20
    
    def get_queryset(self):
        from .permissions import get_user_type
        
        queryset = Evaluation.objects.select_related('matiere', 'classe', 'professeur').order_by('-date_evaluation')
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne voit que les évaluations de sa classe
            return queryset.filter(classe=self.request.user.eleve.classe)
        elif user_type == 'professeur':
            # Un professeur ne voit que ses évaluations
            return queryset.filter(professeur=self.request.user.professeur)
        
        return queryset


class EvaluationDetailView(LoginRequiredMixin, DetailView):
    model = Evaluation
    template_name = 'school_management/evaluation/detail.html'
    context_object_name = 'evaluation'
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne peut voir que les évaluations de sa classe
            if obj.classe != self.request.user.eleve.classe:
                raise PermissionDenied("Vous ne pouvez accéder qu'aux évaluations de votre classe")
        elif user_type == 'professeur':
            # Un professeur ne peut voir que ses évaluations
            if obj.professeur != self.request.user.professeur:
                raise PermissionDenied("Vous ne pouvez accéder qu'à vos propres évaluations")
        elif user_type != 'admin':
            raise PermissionDenied("Accès non autorisé")
        
        return obj
    
    def get_context_data(self, **kwargs):
        from .permissions import get_user_type
        
        context = super().get_context_data(**kwargs)
        evaluation = self.get_object()
        user_type = get_user_type(self.request.user)
        
        # Filtrer les notes selon le type d'utilisateur
        notes_queryset = Note.objects.filter(evaluation=evaluation).select_related('eleve')
        
        if user_type == 'eleve':
            # Un élève ne voit que sa propre note
            notes_queryset = notes_queryset.filter(eleve=self.request.user.eleve)
        
        context['notes'] = notes_queryset
        context['moyenne'] = Note.objects.filter(evaluation=evaluation, note__isnull=False).aggregate(Avg('note'))['note__avg']
        return context


class EvaluationCreateView(LoginRequiredMixin, CreateView):
    model = Evaluation
    template_name = 'school_management/evaluation/form.html'
    fields = ['titre', 'description', 'matiere', 'classe', 'professeur', 'date_evaluation', 'type_evaluation', 'note_sur', 'coefficient']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type == 'eleve':
            raise PermissionDenied("Les élèves ne peuvent pas créer d'évaluations")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Enregistrer le log d'audit
        from .audit_utils import log_model_action
        log_model_action(self.request.user, 'CREATE', self.object, self.request)
        return response


class EvaluationUpdateView(LoginRequiredMixin, UpdateView):
    model = Evaluation
    template_name = 'school_management/evaluation/form.html'
    fields = ['titre', 'description', 'matiere', 'classe', 'professeur', 'date_evaluation', 'type_evaluation', 'note_sur', 'coefficient']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type == 'eleve':
            raise PermissionDenied("Les élèves ne peuvent pas modifier d'évaluations")
        return super().dispatch(request, *args, **kwargs)


class EvaluationDeleteView(LoginRequiredMixin, DeleteView):
    model = Evaluation
    template_name = 'school_management/evaluation/confirm_delete.html'
    success_url = reverse_lazy('school_management:evaluation_list')
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type == 'eleve':
            raise PermissionDenied("Les élèves ne peuvent pas supprimer d'évaluations")
        return super().dispatch(request, *args, **kwargs)


@login_required
def saisir_notes(request, pk):
    """Vue pour saisir les notes d'une évaluation"""
    from .permissions import get_user_type
    
    # Vérifier les permissions - seuls les professeurs et admins peuvent saisir des notes
    user_type = get_user_type(request.user)
    if user_type == 'eleve':
        raise PermissionDenied("Les élèves ne peuvent pas saisir de notes")
    
    evaluation = get_object_or_404(Evaluation, pk=pk)
    eleves = evaluation.classe.eleves.filter(statut=True).order_by('nom', 'prenom')
    
    if request.method == 'POST':
        for eleve in eleves:
            note_value = request.POST.get(f'note_{eleve.id}')
            absent = request.POST.get(f'absent_{eleve.id}') == 'on'
            commentaire = request.POST.get(f'commentaire_{eleve.id}', '')
            
            note, created = Note.objects.get_or_create(
                eleve=eleve,
                evaluation=evaluation,
                defaults={'note': note_value if note_value else None, 'absent': absent, 'commentaire': commentaire}
            )
            
            if not created:
                note.note = note_value if note_value else None
                note.absent = absent
                note.commentaire = commentaire
                note.save()
        
        # Enregistrer le log d'audit
        from .audit_utils import log_notes_save
        notes_count = len([eleve for eleve in eleves if request.POST.get(f'note_{eleve.id}') or request.POST.get(f'absent_{eleve.id}') == 'on'])
        log_notes_save(request.user, evaluation, notes_count, request)
        
        messages.success(request, 'Notes enregistrées avec succès!')
        return redirect('school_management:evaluation_detail', pk=evaluation.pk)
    
    # Récupérer les notes existantes
    notes_existantes = {note.eleve.id: note for note in Note.objects.filter(evaluation=evaluation)}
    
    context = {
        'evaluation': evaluation,
        'eleves': eleves,
        'notes_existantes': notes_existantes,
    }
    return render(request, 'school_management/evaluation/saisir_notes.html', context)


# =============== VUES POUR LES NOTES ===============

class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'school_management/note/list.html'
    context_object_name = 'notes'
    paginate_by = 50
    
    def get_queryset(self):
        from .permissions import get_user_type
        
        queryset = Note.objects.select_related('eleve', 'evaluation', 'evaluation__matiere').order_by('-date_saisie')
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne voit que ses propres notes
            return queryset.filter(eleve=self.request.user.eleve)
        elif user_type == 'professeur':
            # Un professeur ne voit que les notes de ses élèves
            return queryset.filter(eleve__classe__in=self.request.user.professeur.classes.all())
        
        return queryset


@login_required
def notes_eleve(request, eleve_id):
    """Vue pour afficher toutes les notes d'un élève"""
    from .permissions import check_eleve_access
    from django.db.models import Avg
    from collections import defaultdict
    
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    # Vérifier les permissions d'accès
    check_eleve_access(request.user, eleve)
    
    notes = Note.objects.filter(eleve=eleve).select_related('evaluation', 'evaluation__matiere').order_by('-evaluation__date_evaluation')
    
    # Calculer les moyennes par matière
    moyennes_par_matiere = {}
    for note in notes:
        matiere = note.evaluation.matiere
        if matiere not in moyennes_par_matiere:
            # Calculer la moyenne pour cette matière
            notes_matiere = notes.filter(evaluation__matiere=matiere, note__isnull=False)
            if notes_matiere.exists():
                moyenne = notes_matiere.aggregate(moyenne=Avg('note'))['moyenne']
                moyennes_par_matiere[matiere] = round(moyenne, 2) if moyenne else None
            else:
                moyennes_par_matiere[matiere] = None
    
    context = {
        'eleve': eleve,
        'notes': notes,
        'moyennes_par_matiere': moyennes_par_matiere,
    }
    return render(request, 'school_management/note/eleve_notes.html', context)


# =============== VUES POUR LES ABSENCES ===============

class AbsenceListView(LoginRequiredMixin, ListView):
    model = Absence
    template_name = 'school_management/absence/list.html'
    context_object_name = 'absences'
    paginate_by = 20
    
    def get_queryset(self):
        from .permissions import get_user_type
        
        queryset = Absence.objects.select_related('eleve').order_by('-date_debut')
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne voit que ses propres absences
            return queryset.filter(eleve=self.request.user.eleve)
        elif user_type == 'professeur':
            # Un professeur ne voit que les absences de ses élèves
            return queryset.filter(eleve__classe__in=self.request.user.professeur.classes.all())
        
        return queryset


class AbsenceDetailView(LoginRequiredMixin, DetailView):
    model = Absence
    template_name = 'school_management/absence/detail.html'
    context_object_name = 'absence'
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'eleve':
            # Un élève ne peut voir que ses propres absences
            if obj.eleve != self.request.user.eleve:
                raise PermissionDenied("Vous ne pouvez accéder qu'à vos propres données")
        elif user_type == 'professeur':
            # Un professeur ne peut voir que les absences de ses élèves
            if obj.eleve.classe not in self.request.user.professeur.classes.all():
                raise PermissionDenied("Vous ne pouvez accéder qu'aux données de vos élèves")
        elif user_type != 'admin':
            raise PermissionDenied("Accès non autorisé")
        
        return obj


class AbsenceCreateView(LoginRequiredMixin, CreateView):
    model = Absence
    template_name = 'school_management/absence/form.html'
    fields = ['eleve', 'date_debut', 'date_fin', 'motif', 'justifiee', 'commentaire', 'document_justificatif']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type == 'eleve':
            raise PermissionDenied("Les élèves ne peuvent pas créer d'absences")
        return super().dispatch(request, *args, **kwargs)


class AbsenceUpdateView(LoginRequiredMixin, UpdateView):
    model = Absence
    template_name = 'school_management/absence/form.html'
    fields = ['eleve', 'date_debut', 'date_fin', 'motif', 'justifiee', 'commentaire', 'document_justificatif']
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type == 'eleve':
            raise PermissionDenied("Les élèves ne peuvent pas modifier d'absences")
        return super().dispatch(request, *args, **kwargs)


class AbsenceDeleteView(LoginRequiredMixin, DeleteView):
    model = Absence
    template_name = 'school_management/absence/confirm_delete.html'
    success_url = reverse_lazy('school_management:absence_list')
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type == 'eleve':
            raise PermissionDenied("Les élèves ne peuvent pas supprimer d'absences")
        return super().dispatch(request, *args, **kwargs)


# =============== VUES POUR LES RAPPORTS ===============

@login_required
def rapports(request):
    """Vue principale des rapports"""
    context = {
        'classes': Classe.objects.annotate(nb_eleves=Count('eleves')),
        'eleves': Eleve.objects.filter(statut=True).select_related('user', 'classe').order_by('nom', 'prenom'),
        'matieres': Matiere.objects.all().order_by('nom'),
        'stats_generales': {
            'total_eleves': Eleve.objects.filter(statut=True).count(),
            'total_evaluations': Evaluation.objects.count(),
            'total_notes': Note.objects.count(),
            'total_absences': Absence.objects.count(),
        }
    }
    return render(request, 'school_management/rapports/index.html', context)


@login_required
def rapport_classe(request, classe_id):
    """Rapport détaillé d'une classe"""
    classe = get_object_or_404(Classe, pk=classe_id)
    eleves = classe.eleves.filter(statut=True).order_by('nom', 'prenom')
    
    context = {
        'classe': classe,
        'eleves': eleves,
        'evaluations': Evaluation.objects.filter(classe=classe).order_by('-date_evaluation')[:10],
    }
    return render(request, 'school_management/rapports/classe.html', context)


@login_required
def bulletin_eleve(request, eleve_id):
    """Bulletin de notes d'un élève"""
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    notes = Note.objects.filter(eleve=eleve).select_related('evaluation', 'evaluation__matiere')
    
    # Calculer les moyennes par matière
    moyennes_matieres = {}
    for note in notes:
        matiere = note.evaluation.matiere
        if matiere not in moyennes_matieres:
            moyennes_matieres[matiere] = {'notes': [], 'coefficients': []}
        
        if note.note is not None:
            moyennes_matieres[matiere]['notes'].append(float(note.note_sur_20 or 0))
            moyennes_matieres[matiere]['coefficients'].append(float(note.evaluation.coefficient))
    
    # Calculer la moyenne générale
    moyennes_finales = {}
    for matiere, data in moyennes_matieres.items():
        if data['notes']:
            moyenne_ponderee = sum(n * c for n, c in zip(data['notes'], data['coefficients'])) / sum(data['coefficients'])
            moyennes_finales[matiere] = round(moyenne_ponderee, 2)
    
    context = {
        'eleve': eleve,
        'notes': notes.order_by('-evaluation__date_evaluation'),
        'moyennes_matieres': moyennes_finales,
        'moyenne_generale': round(sum(moyennes_finales.values()) / len(moyennes_finales), 2) if moyennes_finales else 0,
    }
    return render(request, 'school_management/rapports/bulletin.html', context)


@method_decorator(csrf_protect, name='dispatch')
class CustomLoginView(LoginView):
    """Vue de connexion personnalisée avec gestion des différents types d'utilisateurs"""
    template_name = 'registration/login.html'
    form_class = CustomLoginForm
    
    def get_context_data(self, **kwargs):
        """Ajoute le contexte nécessaire au template"""
        context = super().get_context_data(**kwargs)
        return context
    
    def form_valid(self, form):
        """Gère la connexion après validation du formulaire"""
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user_type = form.cleaned_data.get('user_type')
        
        if not user_type:
            messages.error(self.request, 'Veuillez sélectionner votre type d\'utilisateur')
            return self.form_invalid(form)
        
        # Authentification selon le type d'utilisateur
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            # Vérifier que l'utilisateur correspond au type sélectionné
            if self.validate_user_type(user, user_type):
                login(self.request, user)
                
                # Redirection selon le type d'utilisateur
                if user_type == 'eleve':
                    return redirect('school_management:eleve_dashboard')
                elif user_type == 'professeur':
                    return redirect('school_management:professeur_dashboard')
                elif user_type == 'parent':
                    return redirect('school_management:parent_dashboard')
                elif user_type == 'admin':
                    return redirect('school_management:dashboard')
                else:
                    return redirect('school_management:dashboard')
            else:
                messages.error(self.request, 'Type d\'utilisateur incorrect pour ces identifiants')
        else:
            if user_type == 'eleve':
                messages.error(self.request, 'Numéro étudiant ou mot de passe incorrect')
            elif user_type == 'professeur':
                messages.error(self.request, 'Nom d\'utilisateur ou mot de passe incorrect')
            elif user_type == 'parent':
                messages.error(self.request, 'Nom d\'utilisateur ou mot de passe incorrect')
            else:
                messages.error(self.request, 'Identifiant ou mot de passe incorrect')
        
        return self.form_invalid(form)
    
    def validate_user_type(self, user, user_type):
        """Valide que l'utilisateur correspond au type sélectionné"""
        try:
            if user_type == 'eleve':
                return hasattr(user, 'eleve')
            elif user_type == 'professeur':
                return hasattr(user, 'professeur')
            elif user_type == 'parent':
                return hasattr(user, 'parent')
            elif user_type == 'admin':
                return user.is_staff or user.is_superuser
            return False
        except:
            return False


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


@login_required
def eleve_dashboard(request):
    """Tableau de bord pour les élèves"""
    try:
        eleve = request.user.eleve
    except:
        messages.error(request, 'Accès non autorisé')
        return redirect('school_management:login')
    
    # Récupérer les données de l'élève
    notes = Note.objects.filter(eleve=eleve).select_related('evaluation', 'evaluation__matiere').order_by('-evaluation__date_evaluation')[:10]
    absences = Absence.objects.filter(eleve=eleve).order_by('-date_debut')[:5]
    evaluations_a_venir = Evaluation.objects.filter(
        classe=eleve.classe,
        date_evaluation__gte=timezone.now().date()
    ).order_by('date_evaluation')[:5]
    
    # Statistiques
    moyenne_generale = notes.aggregate(moyenne=Avg('note'))['moyenne']
    total_absences = Absence.objects.filter(eleve=eleve).count()
    absences_non_justifiees = Absence.objects.filter(eleve=eleve, justifiee=False).count()
    
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
    
    context = {
        'eleve': eleve,
        'notes': notes,
        'absences': absences,
        'evaluations_a_venir': evaluations_a_venir,
        'moyenne_generale': moyenne_generale,
        'total_absences': total_absences,
        'absences_non_justifiees': absences_non_justifiees,
        'conversations_count': conversations_count,
        'unread_messages_count': unread_messages_count,
    }
    
    return render(request, 'school_management/dashboards/eleve.html', context)


@login_required
def professeur_dashboard(request):
    """Tableau de bord pour les professeurs"""
    try:
        professeur = request.user.professeur
    except:
        messages.error(request, 'Accès non autorisé')
        return redirect('school_management:login')
    
    # Récupérer les données du professeur
    classes = professeur.classes.all()
    matieres = professeur.matieres.all()
    evaluations_recentes = Evaluation.objects.filter(professeur=professeur).order_by('-date_evaluation')[:5]
    
    # Statistiques
    total_eleves = sum([classe.eleves.count() for classe in classes])
    total_evaluations = Evaluation.objects.filter(professeur=professeur).count()
    # Compter les évaluations sans notes saisies
    evaluations_sans_notes = []
    for evaluation in Evaluation.objects.filter(professeur=professeur):
        if not evaluation.notes.exists():
            evaluations_sans_notes.append(evaluation)
    notes_a_saisir = len(evaluations_sans_notes)
    
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
    
    context = {
        'professeur': professeur,
        'classes': classes,
        'matieres': matieres,
        'evaluations_recentes': evaluations_recentes,
        'total_eleves': total_eleves,
        'total_evaluations': total_evaluations,
        'notes_a_saisir': notes_a_saisir,
        'conversations_count': conversations_count,
        'unread_messages_count': unread_messages_count,
    }
    
    return render(request, 'school_management/dashboards/professeur.html', context)


@login_required
def audit_logs(request):
    """Vue pour afficher les logs d'audit - réservée aux administrateurs"""
    from .permissions import get_user_type
    from .models import AuditLog
    from django.contrib.auth.models import User
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Vérifier que l'utilisateur est administrateur
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Seuls les administrateurs peuvent consulter les logs d'audit")
    
    # Récupérer les paramètres de filtrage
    search = request.GET.get('search', '')
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Construire la requête
    logs = AuditLog.objects.select_related('user').all()
    
    # Appliquer les filtres
    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(model_name__icontains=search) |
            Q(object_repr__icontains=search) |
            Q(details__icontains=search)
        )
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)  # 50 logs par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_logs = logs.count()
    today_logs = logs.filter(timestamp__date=timezone.now().date()).count()
    
    # Actions les plus fréquentes
    from django.db.models import Count
    frequent_actions = logs.values('action').annotate(count=Count('action')).order_by('-count')[:5]
    
    # Utilisateurs les plus actifs
    active_users = logs.values('user__username', 'user__first_name', 'user__last_name').annotate(
        count=Count('user')
    ).order_by('-count')[:5]
    
    context = {
        'page_obj': page_obj,
        'total_logs': total_logs,
        'today_logs': today_logs,
        'frequent_actions': frequent_actions,
        'active_users': active_users,
        'search': search,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': AuditLog.ACTION_CHOICES,
        'users': User.objects.all().order_by('username'),
    }
    
    return render(request, 'school_management/audit/logs.html', context)


# =============== VUES POUR LES PARENTS ===============

class ParentListView(LoginRequiredMixin, ListView):
    model = Parent
    template_name = 'school_management/parent/list.html'
    context_object_name = 'parents'
    paginate_by = 20
    
    def get_queryset(self):
        from .permissions import get_user_type
        queryset = Parent.objects.filter(actif=True).order_by('nom', 'prenom')
        user_type = get_user_type(self.request.user)
        
        if user_type == 'parent':
            # Un parent ne voit que ses propres informations
            queryset = queryset.filter(user=self.request.user)
        
        return queryset


class ParentDetailView(LoginRequiredMixin, DetailView):
    model = Parent
    template_name = 'school_management/parent/detail.html'
    context_object_name = 'parent'
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'parent':
            # Un parent ne peut voir que ses propres informations
            if obj.user != self.request.user:
                raise PermissionDenied("Vous ne pouvez accéder qu'à vos propres informations.")
        elif user_type == 'eleve':
            # Un élève peut voir les informations de ses parents
            if obj not in self.request.user.eleve.parents.all():
                raise PermissionDenied("Vous ne pouvez accéder qu'aux informations de vos parents.")
        elif user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Accès non autorisé.")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent = self.get_object()
        context['enfants'] = parent.get_enfants()
        return context


class ParentCreateView(LoginRequiredMixin, CreateView):
    model = Parent
    template_name = 'school_management/parent/form.html'
    form_class = ParentForm
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent créer des parents")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Enregistrer le log d'audit
        from .audit_utils import log_model_action
        log_model_action(self.request.user, 'CREATE', self.object, self.request)
        return response


class ParentUpdateView(LoginRequiredMixin, UpdateView):
    model = Parent
    template_name = 'school_management/parent/form.html'
    form_class = ParentForm
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'parent']:
            raise PermissionDenied("Accès non autorisé")
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'parent':
            # Un parent ne peut modifier que ses propres informations
            if obj.user != self.request.user:
                raise PermissionDenied("Vous ne pouvez modifier que vos propres informations.")
        
        return obj
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Enregistrer le log d'audit
        from .audit_utils import log_model_action
        log_model_action(self.request.user, 'UPDATE', self.object, self.request)
        return response


class ParentDeleteView(LoginRequiredMixin, DeleteView):
    model = Parent
    template_name = 'school_management/parent/confirm_delete.html'
    success_url = reverse_lazy('school_management:parent_list')
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type not in ['admin']:
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des parents")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        # Enregistrer le log d'audit avant suppression
        from .audit_utils import log_model_action
        obj = self.get_object()
        log_model_action(request.user, 'DELETE', obj, request)
        return super().delete(request, *args, **kwargs)


# =============== VUES POUR LES COMMUNICATIONS ===============

class CommunicationListView(LoginRequiredMixin, ListView):
    model = Communication
    template_name = 'school_management/communication/list.html'
    context_object_name = 'communications'
    paginate_by = 10
    
    def get_queryset(self):
        from .permissions import get_user_type
        user_type = get_user_type(self.request.user)
        
        # Filtrer les communications selon le type d'utilisateur
        queryset = Communication.objects.filter(active=True).order_by('-date_creation')
        
        if user_type == 'eleve':
            # Un élève voit les communications pour tous, élèves, ou sa classe
            eleve = self.request.user.eleve
            queryset = queryset.filter(
                Q(destinataires__in=['TOUS', 'ELEVES']) |
                Q(destinataires='CLASSE', classe_cible=eleve.classe)
            )
        elif user_type == 'parent':
            # Un parent voit les communications pour tous ou parents
            queryset = queryset.filter(destinataires__in=['TOUS', 'PARENTS'])
        elif user_type == 'professeur':
            # Un professeur voit les communications pour tous, professeurs, ou ses classes
            professeur = self.request.user.professeur
            queryset = queryset.filter(
                Q(destinataires__in=['TOUS', 'PROFESSEURS']) |
                Q(destinataires='CLASSE', classe_cible__in=professeur.classes.all())
            )
        elif user_type == 'admin':
            # Un admin voit toutes les communications
            pass
        
        # Filtrer par date de publication et expiration
        now = timezone.now()
        queryset = queryset.filter(
            Q(date_publication__isnull=True) | Q(date_publication__lte=now)
        ).filter(
            Q(date_expiration__isnull=True) | Q(date_expiration__gte=now)
        )
        
        return queryset


class CommunicationDetailView(LoginRequiredMixin, DetailView):
    model = Communication
    template_name = 'school_management/communication/detail.html'
    context_object_name = 'communication'
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        # Vérifier que l'utilisateur peut voir cette communication
        if not obj.is_publiee():
            raise PermissionDenied("Cette communication n'est pas disponible.")
        
        if user_type == 'eleve':
            eleve = self.request.user.eleve
            if not (obj.destinataires in ['TOUS', 'ELEVES'] or 
                   (obj.destinataires == 'CLASSE' and obj.classe_cible == eleve.classe)):
                raise PermissionDenied("Vous n'avez pas accès à cette communication.")
        elif user_type == 'parent':
            if obj.destinataires not in ['TOUS', 'PARENTS']:
                raise PermissionDenied("Vous n'avez pas accès à cette communication.")
        elif user_type == 'professeur':
            professeur = self.request.user.professeur
            if not (obj.destinataires in ['TOUS', 'PROFESSEURS'] or 
                   (obj.destinataires == 'CLASSE' and obj.classe_cible in professeur.classes.all())):
                raise PermissionDenied("Vous n'avez pas accès à cette communication.")
        elif user_type != 'admin':
            raise PermissionDenied("Accès non autorisé.")
        
        return obj


class CommunicationCreateView(LoginRequiredMixin, CreateView):
    model = Communication
    template_name = 'school_management/communication/form.html'
    form_class = CommunicationForm
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Seuls les administrateurs et professeurs peuvent créer des communications")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.auteur = self.request.user
        response = super().form_valid(form)
        # Enregistrer le log d'audit
        from .audit_utils import log_model_action
        log_model_action(self.request.user, 'CREATE', self.object, self.request)
        return response


class CommunicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Communication
    template_name = 'school_management/communication/form.html'
    form_class = CommunicationForm
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Seuls les administrateurs et professeurs peuvent modifier des communications")
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'professeur':
            # Un professeur ne peut modifier que ses propres communications
            if obj.auteur != self.request.user:
                raise PermissionDenied("Vous ne pouvez modifier que vos propres communications.")
        
        return obj
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Enregistrer le log d'audit
        from .audit_utils import log_model_action
        log_model_action(self.request.user, 'UPDATE', self.object, self.request)
        return response


class CommunicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Communication
    template_name = 'school_management/communication/confirm_delete.html'
    success_url = reverse_lazy('school_management:communication_list')
    
    def dispatch(self, request, *args, **kwargs):
        from .permissions import get_user_type
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'professeur']:
            raise PermissionDenied("Seuls les administrateurs et professeurs peuvent supprimer des communications")
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        from .permissions import get_user_type
        obj = super().get_object(queryset)
        user_type = get_user_type(self.request.user)
        
        if user_type == 'professeur':
            # Un professeur ne peut supprimer que ses propres communications
            if obj.auteur != self.request.user:
                raise PermissionDenied("Vous ne pouvez supprimer que vos propres communications.")
        
        return obj
    
    def delete(self, request, *args, **kwargs):
        # Enregistrer le log d'audit avant suppression
        from .audit_utils import log_model_action
        obj = self.get_object()
        log_model_action(request.user, 'DELETE', obj, request)
        return super().delete(request, *args, **kwargs)


# =============== VUES POUR LA GESTION DES PROFILS ===============

@login_required
def user_profile(request):
    """Vue pour afficher et modifier le profil utilisateur"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('school_management:user_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'user_type': user_type,
    }
    
    return render(request, 'school_management/profile/user_profile.html', context)


@login_required
def change_password(request):
    """Vue pour changer le mot de passe"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Votre mot de passe a été changé avec succès.')
            return redirect('school_management:user_profile')
    else:
        form = PasswordChangeForm(user=request.user)
    
    context = {
        'form': form,
        'user_type': user_type,
    }
    
    return render(request, 'school_management/profile/change_password.html', context)


@login_required
def generate_bulletin(request, eleve_id):
    """Vue pour générer automatiquement un bulletin pour un élève"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    eleve = get_object_or_404(Eleve, id=eleve_id)
    
    # Vérifier les permissions
    if user_type == 'eleve' and request.user.eleve != eleve:
        raise PermissionDenied("Vous ne pouvez générer que votre propre bulletin.")
    elif user_type == 'parent':
        if not eleve.parents.filter(user=request.user).exists():
            raise PermissionDenied("Vous ne pouvez générer que les bulletins de vos enfants.")
    elif user_type not in ['professeur', 'admin']:
        raise PermissionDenied("Accès non autorisé.")
    
    # Récupérer les notes de l'élève pour la période actuelle
    notes = Note.objects.filter(
        eleve=eleve,
        evaluation__date_evaluation__year=timezone.now().year
    ).select_related('evaluation', 'evaluation__matiere')
    
    if not notes.exists():
        messages.warning(request, f"Aucune note trouvée pour {eleve.get_full_name()} pour l'année en cours.")
        return redirect('school_management:eleve_detail', pk=eleve_id)
    
    # Calculer les moyennes par matière
    matieres_notes = {}
    for note in notes:
        matiere = note.evaluation.matiere
        if matiere not in matieres_notes:
            matieres_notes[matiere] = []
        matieres_notes[matiere].append(note.note)
    
    # Calculer les moyennes
    moyennes_par_matiere = {}
    for matiere, notes_list in matieres_notes.items():
        moyennes_par_matiere[matiere] = sum(notes_list) / len(notes_list)
    
    # Calculer la moyenne générale
    if moyennes_par_matiere:
        moyenne_generale = sum(moyennes_par_matiere.values()) / len(moyennes_par_matiere)
    else:
        moyenne_generale = 0
    
    # Calculer le rang dans la classe
    eleves_classe = Eleve.objects.filter(classe=eleve.classe)
    rangs = []
    for e in eleves_classe:
        e_notes = Note.objects.filter(
            eleve=e,
            evaluation__date_evaluation__year=timezone.now().year
        )
        if e_notes.exists():
            e_moyennes = {}
            for note in e_notes:
                matiere = note.evaluation.matiere
                if matiere not in e_moyennes:
                    e_moyennes[matiere] = []
                e_moyennes[matiere].append(note.note)
            
            e_moyenne_gen = 0
            if e_moyennes:
                moyennes = [sum(notes) / len(notes) for notes in e_moyennes.values()]
                e_moyenne_gen = sum(moyennes) / len(moyennes)
            
            rangs.append((e, e_moyenne_gen))
    
    # Trier par moyenne décroissante
    rangs.sort(key=lambda x: x[1], reverse=True)
    
    # Trouver le rang de l'élève
    rang = 1
    for i, (e, moy) in enumerate(rangs):
        if e == eleve:
            rang = i + 1
            break
    
    # Calculer la moyenne de la classe
    if rangs:
        moyenne_classe = sum([moy for _, moy in rangs]) / len(rangs)
    else:
        moyenne_classe = 0
    
    # Année scolaire actuelle
    current_year = timezone.now().year
    annee_scolaire = f"{current_year}/{current_year + 1}"
    
    # Calculer la moyenne en pourcentage
    moyenne_pourcentage = (moyenne_generale / 20) * 100
    
    # Déterminer la mention
    mention = ""
    couleur_mention = ""
    icone_mention = ""
    
    if moyenne_generale >= 18:
        mention = "EXCELLENT"
        couleur_mention = "success"
        icone_mention = "fas fa-star"
    elif moyenne_generale >= 16:
        mention = "TRÈS BIEN"
        couleur_mention = "primary"
        icone_mention = "fas fa-thumbs-up"
    elif moyenne_generale >= 14:
        mention = "BIEN"
        couleur_mention = "info"
        icone_mention = "fas fa-check"
    elif moyenne_generale >= 12:
        mention = "ASSEZ BIEN"
        couleur_mention = "warning"
        icone_mention = "fas fa-exclamation-triangle"
    elif moyenne_generale >= 10:
        mention = "PASSABLE"
        couleur_mention = "secondary"
        icone_mention = "fas fa-minus"
    else:
        mention = "INSUFFISANT"
        couleur_mention = "danger"
        icone_mention = "fas fa-times"
    
    # Déterminer la décision de passage
    decision_passage = ""
    couleur_decision = ""
    icone_decision = ""
    
    # Compter les échecs (notes < 10)
    echecs = 0
    for matiere, moyenne in moyennes_par_matiere.items():
        if moyenne < 10:
            echecs += 1
    
    if moyenne_pourcentage < 50:
        # Inférieur à 50% : redoublement
        decision_passage = "REDOUBLE"
        couleur_decision = "danger"
        icone_decision = "fas fa-times-circle"
    elif moyenne_pourcentage < 60:
        # Entre 50% et 60% : seconde session si échecs, sinon passage
        if echecs > 0:
            decision_passage = "SECONDE SESSION"
            couleur_decision = "warning"
            icone_decision = "fas fa-exclamation-triangle"
        else:
            decision_passage = "PASSE EN CLASSE SUPERIEURE"
            couleur_decision = "success"
            icone_decision = "fas fa-check-circle"
    else:
        # Supérieur à 60% : passage
        decision_passage = "PASSE EN CLASSE SUPERIEURE"
        couleur_decision = "success"
        icone_decision = "fas fa-check-circle"
    
    context = {
        'eleve': eleve,
        'moyennes_par_matiere': moyennes_par_matiere,
        'moyenne_generale': moyenne_generale,
        'moyenne_pourcentage': moyenne_pourcentage,
        'rang': rang,
        'moyenne_classe': moyenne_classe,
        'total_eleves_classe': len(rangs),
        'notes': notes,
        'user_type': user_type,
        'annee_scolaire': annee_scolaire,
        'mention': mention,
        'couleur_mention': couleur_mention,
        'icone_mention': icone_mention,
        'decision_passage': decision_passage,
        'couleur_decision': couleur_decision,
        'icone_decision': icone_decision,
        'echecs': echecs,
        'total_matieres': len(moyennes_par_matiere),
    }
    
    return render(request, 'school_management/bulletin/generate.html', context)


@login_required
def absence_statistics(request):
    """Vue pour afficher les statistiques d'absences détaillées"""
    from .permissions import get_user_type
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    user_type = get_user_type(request.user)
    
    # Statistiques générales
    total_absences = Absence.objects.count()
    absences_justifiees = Absence.objects.filter(justifiee=True).count()
    absences_non_justifiees = Absence.objects.filter(justifiee=False).count()
    
    # Absences par mois (6 derniers mois)
    six_months_ago = timezone.now() - timedelta(days=180)
    absences_par_mois = []
    for i in range(6):
        mois_date = timezone.now() - timedelta(days=30*i)
        mois_debut = mois_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            mois_fin = timezone.now()
        else:
            mois_fin = (mois_debut + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = Absence.objects.filter(
            date_debut__gte=mois_debut,
            date_debut__lte=mois_fin
        ).count()
        
        absences_par_mois.append({
            'mois': mois_debut.strftime('%B %Y'),
            'count': count
        })
    
    absences_par_mois.reverse()
    
    # Top 10 des élèves avec le plus d'absences
    top_absences_eleves = Eleve.objects.annotate(
        total_absences=Count('absences')
    ).order_by('-total_absences')[:10]
    
    # Absences par classe
    absences_par_classe = []
    for classe in Classe.objects.all():
        total_absences = Absence.objects.filter(eleve__classe=classe).count()
        nb_eleves = classe.eleves.count()
        moyenne_par_eleve = total_absences / nb_eleves if nb_eleves > 0 else 0
        
        absences_par_classe.append({
            'classe': classe,
            'total_absences': total_absences,
            'nb_eleves': nb_eleves,
            'moyenne_par_eleve': moyenne_par_eleve
        })
    
    # Trier par nombre total d'absences
    absences_par_classe.sort(key=lambda x: x['total_absences'], reverse=True)
    
    # Absences par jour de la semaine
    absences_par_jour = []
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    for i, jour in enumerate(jours):
        count = Absence.objects.filter(
            date_debut__week_day=i+2  # Django week_day: 2=Lundi, 3=Mardi, etc.
        ).count()
        absences_par_jour.append({'jour': jour, 'count': count})
    
    # Absences récentes
    absences_recentes = Absence.objects.select_related('eleve', 'eleve__classe').order_by('-date_debut')[:10]
    
    context = {
        'user_type': user_type,
        'total_absences': total_absences,
        'absences_justifiees': absences_justifiees,
        'absences_non_justifiees': absences_non_justifiees,
        'taux_justification': (absences_justifiees / total_absences * 100) if total_absences > 0 else 0,
        'absences_par_mois': absences_par_mois,
        'top_absences_eleves': top_absences_eleves,
        'absences_par_classe': absences_par_classe,
        'absences_par_jour': absences_par_jour,
        'absences_recentes': absences_recentes,
    }
    
    return render(request, 'school_management/statistics/absence_statistics.html', context)


@login_required
def export_user_data(request):
    """Vue pour exporter les données utilisateurs"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs")
    
    import csv
    from django.http import HttpResponse
    
    # Créer la réponse HTTP avec le type CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="donnees_utilisateurs.csv"'
    
    writer = csv.writer(response)
    
    # En-têtes
    writer.writerow(['Type', 'Nom d\'utilisateur', 'Prénom', 'Nom', 'Email', 'Date d\'inscription', 'Dernière connexion', 'Actif'])
    
    # Exporter tous les utilisateurs
    users = User.objects.all().order_by('date_joined')
    for user in users:
        user_type = get_user_type(user)
        writer.writerow([
            user_type,
            user.username,
            user.first_name,
            user.last_name,
            user.email,
            user.date_joined.strftime('%d/%m/%Y %H:%M'),
            user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Jamais',
            'Oui' if user.is_active else 'Non'
        ])
    
    return response


@login_required
def sync_user_accounts(request):
    """Vue pour synchroniser les comptes utilisateurs"""
    from .permissions import get_user_type
    
    user_type = get_user_type(request.user)
    if user_type != 'admin':
        raise PermissionDenied("Accès réservé aux administrateurs")
    
    if request.method == 'POST':
        # Créer des comptes utilisateurs pour les profils sans compte
        created_count = 0
        
        # Synchroniser les élèves
        eleves_sans_compte = Eleve.objects.filter(user__isnull=True)
        for eleve in eleves_sans_compte:
            username = f"eleve_{eleve.numero_eleve}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    first_name=eleve.prenom,
                    last_name=eleve.nom,
                    email=f"{username}@ecole.local"
                )
                eleve.user = user
                eleve.save()
                created_count += 1
        
        # Synchroniser les professeurs
        profs_sans_compte = Professeur.objects.filter(user__isnull=True)
        for prof in profs_sans_compte:
            username = f"prof_{prof.id}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    first_name=prof.prenom,
                    last_name=prof.nom,
                    email=f"{username}@ecole.local"
                )
                prof.user = user
                prof.save()
                created_count += 1
        
        # Synchroniser les parents
        parents_sans_compte = Parent.objects.filter(user__isnull=True)
        for parent in parents_sans_compte:
            username = f"parent_{parent.id}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    first_name=parent.prenom,
                    last_name=parent.nom,
                    email=f"{username}@ecole.local"
                )
                parent.user = user
                parent.save()
                created_count += 1
        
        messages.success(request, f"Synchronisation terminée. {created_count} comptes créés.")
        return redirect('school_management:admin_users')
    
    # Afficher la page de confirmation
    eleves_sans_compte = Eleve.objects.filter(user__isnull=True).count()
    profs_sans_compte = Professeur.objects.filter(user__isnull=True).count()
    parents_sans_compte = Parent.objects.filter(user__isnull=True).count()
    total_sans_compte = eleves_sans_compte + profs_sans_compte + parents_sans_compte
    
    context = {
        'eleves_sans_compte': eleves_sans_compte,
        'profs_sans_compte': profs_sans_compte,
        'parents_sans_compte': parents_sans_compte,
        'total_sans_compte': total_sans_compte,
    }
    
    return render(request, 'school_management/admin/sync_accounts.html', context)


@login_required
def results_analysis(request):
    """Vue pour l'analyse des résultats et performances"""
    from .permissions import get_user_type
    from django.db.models import Avg, Count, Q, Min, Max
    
    user_type = get_user_type(request.user)
    
    # Statistiques générales des notes
    total_notes = Note.objects.count()
    moyenne_generale = Note.objects.aggregate(avg=Avg('note'))['avg'] or 0
    note_min = Note.objects.aggregate(min=Min('note'))['min'] or 0
    note_max = Note.objects.aggregate(max=Max('note'))['max'] or 0
    
    # Répartition des notes par tranches
    excellent = Note.objects.filter(note__gte=16).count()
    tres_bien = Note.objects.filter(note__gte=14, note__lt=16).count()
    bien = Note.objects.filter(note__gte=12, note__lt=14).count()
    assez_bien = Note.objects.filter(note__gte=10, note__lt=12).count()
    insuffisant = Note.objects.filter(note__lt=10).count()
    
    # Top 10 des meilleurs élèves (moyenne générale)
    meilleurs_eleves = []
    for eleve in Eleve.objects.all():
        notes_eleve = Note.objects.filter(eleve=eleve)
        if notes_eleve.exists():
            moyenne = notes_eleve.aggregate(avg=Avg('note'))['avg']
            meilleurs_eleves.append({
                'eleve': eleve,
                'moyenne': moyenne,
                'nb_notes': notes_eleve.count()
            })
    
    # Trier par moyenne décroissante
    meilleurs_eleves.sort(key=lambda x: x['moyenne'], reverse=True)
    meilleurs_eleves = meilleurs_eleves[:10]
    
    # Top 10 des élèves en difficulté
    eleves_difficulte = []
    for eleve in Eleve.objects.all():
        notes_eleve = Note.objects.filter(eleve=eleve)
        if notes_eleve.exists():
            moyenne = notes_eleve.aggregate(avg=Avg('note'))['avg']
            if moyenne < 10:  # Seulement les élèves en difficulté
                eleves_difficulte.append({
                    'eleve': eleve,
                    'moyenne': moyenne,
                    'nb_notes': notes_eleve.count()
                })
    
    # Trier par moyenne croissante (les plus en difficulté en premier)
    eleves_difficulte.sort(key=lambda x: x['moyenne'])
    eleves_difficulte = eleves_difficulte[:10]
    
    # Performance par matière
    performance_matieres = []
    for matiere in Matiere.objects.all():
        notes_matiere = Note.objects.filter(evaluation__matiere=matiere)
        if notes_matiere.exists():
            stats = notes_matiere.aggregate(
                moyenne=Avg('note'),
                min=Min('note'),
                max=Max('note'),
                count=Count('note')
            )
            performance_matieres.append({
                'matiere': matiere,
                'moyenne': stats['moyenne'],
                'min': stats['min'],
                'max': stats['max'],
                'count': stats['count']
            })
    
    # Trier par moyenne décroissante
    performance_matieres.sort(key=lambda x: x['moyenne'], reverse=True)
    
    # Performance par classe
    performance_classes = []
    for classe in Classe.objects.all():
        eleves_classe = classe.eleves.all()
        if eleves_classe.exists():
            notes_classe = Note.objects.filter(eleve__in=eleves_classe)
            if notes_classe.exists():
                stats = notes_classe.aggregate(
                    moyenne=Avg('note'),
                    min=Min('note'),
                    max=Max('note'),
                    count=Count('note')
                )
                performance_classes.append({
                    'classe': classe,
                    'moyenne': stats['moyenne'],
                    'min': stats['min'],
                    'max': stats['max'],
                    'count': stats['count'],
                    'nb_eleves': eleves_classe.count()
                })
    
    # Trier par moyenne décroissante
    performance_classes.sort(key=lambda x: x['moyenne'], reverse=True)
    
    # Évolution des moyennes par mois (6 derniers mois)
    from datetime import datetime, timedelta
    evolution_moyennes = []
    for i in range(6):
        mois_date = timezone.now() - timedelta(days=30*i)
        mois_debut = mois_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            mois_fin = timezone.now()
        else:
            mois_fin = (mois_debut + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        notes_mois = Note.objects.filter(
            date_saisie__gte=mois_debut,
            date_saisie__lte=mois_fin
        )
        
        moyenne_mois = notes_mois.aggregate(avg=Avg('note'))['avg'] if notes_mois.exists() else 0
        
        evolution_moyennes.append({
            'mois': mois_debut.strftime('%B %Y'),
            'moyenne': moyenne_mois,
            'nb_notes': notes_mois.count()
        })
    
    evolution_moyennes.reverse()
    
    # Taux de réussite par classe
    taux_reussite_classes = []
    for classe in Classe.objects.all():
        eleves_classe = classe.eleves.all()
        if eleves_classe.exists():
            eleves_reussite = 0
            for eleve in eleves_classe:
                notes_eleve = Note.objects.filter(eleve=eleve)
                if notes_eleve.exists():
                    moyenne = notes_eleve.aggregate(avg=Avg('note'))['avg']
                    if moyenne >= 10:
                        eleves_reussite += 1
            
            taux_reussite = (eleves_reussite / eleves_classe.count()) * 100 if eleves_classe.count() > 0 else 0
            
            taux_reussite_classes.append({
                'classe': classe,
                'taux_reussite': taux_reussite,
                'eleves_reussite': eleves_reussite,
                'total_eleves': eleves_classe.count()
            })
    
    # Trier par taux de réussite décroissant
    taux_reussite_classes.sort(key=lambda x: x['taux_reussite'], reverse=True)
    
    context = {
        'user_type': user_type,
        'total_notes': total_notes,
        'moyenne_generale': moyenne_generale,
        'note_min': note_min,
        'note_max': note_max,
        'excellent': excellent,
        'tres_bien': tres_bien,
        'bien': bien,
        'assez_bien': assez_bien,
        'insuffisant': insuffisant,
        'meilleurs_eleves': meilleurs_eleves,
        'eleves_difficulte': eleves_difficulte,
        'performance_matieres': performance_matieres,
        'performance_classes': performance_classes,
        'evolution_moyennes': evolution_moyennes,
        'taux_reussite_classes': taux_reussite_classes,
    }
    
    return render(request, 'school_management/statistics/results_analysis.html', context)
