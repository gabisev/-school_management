from django import forms
from django.forms import modelformset_factory
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import models
from .models import (
    Classe, Matiere, Professeur, Eleve, 
    Evaluation, Note, Absence, Parent, Communication,
    Bulletin, NoteBulletin, Salle, Creneau, EmploiDuTemps,
    EvenementCalendrier, ReservationSalle, Conversation, Participant, Message
)


class EleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'date_naissance', 'lieu_naissance', 'sexe', 'nationalite',
            'numero_etudiant', 'classe', 'adresse', 'telephone', 'email',
            'nom_pere', 'telephone_pere', 'profession_pere',
            'nom_mere', 'telephone_mere', 'profession_mere', 'photo'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_etudiant': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nom_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'profession_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_mere': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_mere': forms.TextInput(attrs={'class': 'form-control'}),
            'profession_mere': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProfesseurForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        label="Prénom",
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    last_name = forms.CharField(
        max_length=30, 
        label="Nom",
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True})
    )
    username = forms.CharField(
        max_length=150, 
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )

    class Meta:
        model = Professeur
        fields = ['civilite', 'telephone', 'adresse', 'date_embauche', 'matieres', 'classes', 'photo']
        widgets = {
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'civilite': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'matieres': forms.CheckboxSelectMultiple(),
            'classes': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Vérifier si le nom d'utilisateur existe déjà
            existing_user = User.objects.filter(username=username)
            if self.instance.pk and self.instance.user:
                existing_user = existing_user.exclude(pk=self.instance.user.pk)
            
            if existing_user.exists():
                raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username

    def save(self, commit=True):
        professeur = super().save(commit=False)
        
        try:
            if not professeur.user_id:
                # Créer un nouvel utilisateur
                user = User.objects.create_user(
                    username=self.cleaned_data['username'],
                    email=self.cleaned_data['email'],
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    password='temp123'  # Mot de passe temporaire
                )
                professeur.user = user
            else:
                # Mettre à jour l'utilisateur existant
                user = professeur.user
                user.first_name = self.cleaned_data['first_name']
                user.last_name = self.cleaned_data['last_name']
                user.email = self.cleaned_data['email']
                user.username = self.cleaned_data['username']
                if commit:
                    user.save()

            if commit:
                professeur.save()
                self.save_m2m()
            return professeur
        except Exception as e:
            raise forms.ValidationError(f"Erreur lors de la création du professeur: {str(e)}")


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'niveau', 'annee_scolaire', 'effectif_max']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau': forms.TextInput(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control'}),
            'effectif_max': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class MatiereForm(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = ['nom', 'code', 'coefficient', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['titre', 'description', 'matiere', 'classe', 'professeur', 'date_evaluation', 'type_evaluation', 'note_sur', 'coefficient']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'professeur': forms.Select(attrs={'class': 'form-control'}),
            'date_evaluation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'type_evaluation': forms.Select(attrs={'class': 'form-control'}),
            'note_sur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['note', 'absent', 'commentaire']
        widgets = {
            'note': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# Formset pour saisir plusieurs notes à la fois
NoteFormSet = modelformset_factory(
    Note, 
    form=NoteForm, 
    extra=0,
    can_delete=False
)


class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ['eleve', 'date_debut', 'date_fin', 'motif', 'justifiee', 'commentaire', 'document_justificatif']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'motif': forms.Select(attrs={'class': 'form-control'}),
            'justifiee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_debut(self):
        date_debut = self.cleaned_data.get('date_debut')
        if date_debut and not hasattr(date_debut, 'tzinfo'):
            from django.utils import timezone
            if timezone.is_aware(date_debut):
                date_debut = timezone.make_naive(date_debut)
        return date_debut

    def clean_date_fin(self):
        date_fin = self.cleaned_data.get('date_fin')
        if date_fin and not hasattr(date_fin, 'tzinfo'):
            from django.utils import timezone
            if timezone.is_aware(date_fin):
                date_fin = timezone.make_naive(date_fin)
        return date_fin

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_debut >= date_fin:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")

        return cleaned_data


class RechercheForm(forms.Form):
    """Formulaire de recherche générique"""
    search = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...'
        })
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=False,
        empty_label="Toutes les classes",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ParentForm(forms.ModelForm):
    """Formulaire pour créer/modifier un parent"""
    first_name = forms.CharField(max_length=30, label="Prénom", widget=forms.TextInput(attrs={'class': 'form-control', 'required': True}))
    last_name = forms.CharField(max_length=30, label="Nom", widget=forms.TextInput(attrs={'class': 'form-control', 'required': True}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True}))
    username = forms.CharField(max_length=150, label="Nom d'utilisateur", widget=forms.TextInput(attrs={'class': 'form-control', 'required': True}))
    enfants = forms.ModelMultipleChoiceField(
        queryset=None,
        label="Enfants",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Sélectionnez les enfants de ce parent. Le mot de passe sera automatiquement défini sur le numéro du premier enfant sélectionné."
    )
    
    class Meta:
        model = Parent
        fields = ['sexe', 'date_naissance', 'lieu_naissance', 'nationalite', 'profession', 'telephone', 'adresse', 'relation', 'photo']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'relation': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir le queryset pour les enfants
        from .models import Eleve
        self.fields['enfants'].queryset = Eleve.objects.filter(statut=True).order_by('nom', 'prenom')
        
        if self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username
            # Pré-sélectionner les enfants existants
            self.fields['enfants'].initial = self.instance.eleves.all()
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            existing_user = User.objects.filter(username=username)
            if self.instance.pk and self.instance.user:
                existing_user = existing_user.exclude(pk=self.instance.user.pk)
            if existing_user.exists():
                raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username
    
    def save(self, commit=True):
        parent = super().save(commit=False)
        try:
            # Récupérer les enfants sélectionnés
            enfants_selectionnes = self.cleaned_data.get('enfants', [])
            
            if not parent.user_id:
                # Déterminer le mot de passe automatique (numéro du premier enfant)
                mot_de_passe = 'parent123'  # Mot de passe par défaut
                if enfants_selectionnes:
                    premier_enfant = enfants_selectionnes[0]
                    mot_de_passe = premier_enfant.numero_etudiant
                
                user = User.objects.create_user(
                    username=self.cleaned_data['username'],
                    email=self.cleaned_data['email'],
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    password=mot_de_passe
                )
                parent.user = user
            else:
                user = parent.user
                user.first_name = self.cleaned_data['first_name']
                user.last_name = self.cleaned_data['last_name']
                user.email = self.cleaned_data['email']
                user.username = self.cleaned_data['username']
                
                # Mettre à jour le mot de passe si des enfants sont sélectionnés
                if enfants_selectionnes:
                    premier_enfant = enfants_selectionnes[0]
                    user.set_password(premier_enfant.numero_etudiant)
                
                if commit:
                    user.save()
            
            if commit:
                parent.save()
                # Gérer la relation ManyToMany avec les enfants
                if enfants_selectionnes:
                    parent.eleves.set(enfants_selectionnes)
                else:
                    parent.eleves.clear()
                    
            return parent
        except Exception as e:
            raise forms.ValidationError(f"Erreur lors de la création/modification du parent: {str(e)}")


class CommunicationForm(forms.ModelForm):
    """Formulaire pour créer/modifier une communication"""
    
    class Meta:
        model = Communication
        fields = ['titre', 'contenu', 'type_communication', 'priorite', 'destinataires', 'classe_cible', 'date_publication', 'date_expiration', 'piece_jointe']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la communication'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Contenu de la communication'}),
            'type_communication': forms.Select(attrs={'class': 'form-control'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'destinataires': forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleClasseField()'}),
            'classe_cible': forms.Select(attrs={'class': 'form-control', 'style': 'display: none;'}),
            'date_publication': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'date_expiration': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'piece_jointe': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les classes pour le champ classe_cible
        self.fields['classe_cible'].queryset = Classe.objects.all().order_by('niveau', 'nom')
        self.fields['classe_cible'].empty_label = "Sélectionner une classe"
        
        # Afficher le champ classe_cible si destinataires = 'CLASSE'
        if self.instance.pk and self.instance.destinataires == 'CLASSE':
            self.fields['classe_cible'].widget.attrs['style'] = 'display: block;'
    
    def clean(self):
        cleaned_data = super().clean()
        destinataires = cleaned_data.get('destinataires')
        classe_cible = cleaned_data.get('classe_cible')
        
        # Vérifier que si destinataires = 'CLASSE', une classe est sélectionnée
        if destinataires == 'CLASSE' and not classe_cible:
            raise forms.ValidationError("Vous devez sélectionner une classe quand les destinataires sont 'Classe spécifique'.")
        
        # Vérifier les dates
        date_publication = cleaned_data.get('date_publication')
        date_expiration = cleaned_data.get('date_expiration')
        
        if date_publication and date_expiration and date_publication >= date_expiration:
            raise forms.ValidationError("La date d'expiration doit être postérieure à la date de publication.")
        
        return cleaned_data


class CustomLoginForm(forms.Form):
    """Formulaire de connexion personnalisé avec sélection du type d'utilisateur"""
    USER_TYPE_CHOICES = [
        ('eleve', 'Élève'),
        ('professeur', 'Professeur'),
        ('parent', 'Parent'),
        ('admin', 'Administrateur'),
    ]
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur',
            'id': 'username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe',
            'id': 'password',
            'autocomplete': 'current-password'
        })
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'user_type'
        })
    )
    
    def __init__(self, *args, **kwargs):
        # Extraire 'request' des kwargs s'il existe (passé par LoginView)
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Définir des placeholders dynamiques selon le type d'utilisateur
        self.fields['username'].widget.attrs['placeholder'] = 'Nom d\'utilisateur'


# ===== FORMULAIRES POUR LES BULLETINS =====

class BulletinForm(forms.ModelForm):
    """Formulaire pour modifier un bulletin"""
    
    class Meta:
        model = Bulletin
        fields = [
            'appreciation_generale',
            'appreciation_prof_principal',
            'statut'
        ]
        widgets = {
            'appreciation_generale': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Appréciation générale sur le travail de l\'élève...'
            }),
            'appreciation_prof_principal': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Appréciation du professeur principal...'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'appreciation_generale': 'Appréciation générale',
            'appreciation_prof_principal': 'Appréciation du professeur principal',
            'statut': 'Statut du bulletin'
        }


class NoteBulletinForm(forms.ModelForm):
    """Formulaire pour une note de bulletin"""
    
    class Meta:
        model = NoteBulletin
        fields = ['appreciation']
        widgets = {
            'appreciation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Appréciation pour cette matière...'
            })
        }
        labels = {
            'appreciation': 'Appréciation'
        }


# Créer le formset pour les notes de bulletin
NoteBulletinFormSet = forms.modelformset_factory(
    NoteBulletin,
    form=NoteBulletinForm,
    extra=0,
    can_delete=False
)


# =============== FORMULAIRES POUR LES PLANNINGS ===============

class SalleForm(forms.ModelForm):
    class Meta:
        model = Salle
        fields = [
            'nom', 'numero', 'capacite', 'type_salle', 
            'equipements', 'accessible_handicap', 'active'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'capacite': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'type_salle': forms.Select(attrs={'class': 'form-control'}),
            'equipements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'accessible_handicap': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CreneauForm(forms.ModelForm):
    class Meta:
        model = Creneau
        fields = ['jour', 'heure_debut', 'heure_fin', 'duree_minutes', 'pause']
        widgets = {
            'jour': forms.Select(attrs={'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duree_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'max': 180}),
            'pause': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        
        if heure_debut and heure_fin:
            if heure_debut >= heure_fin:
                raise forms.ValidationError("L'heure de fin doit être postérieure à l'heure de début.")
        
        return cleaned_data


class EmploiDuTempsForm(forms.ModelForm):
    class Meta:
        model = EmploiDuTemps
        fields = [
            'classe', 'matiere', 'professeur', 'salle', 'creneau',
            'type_cours', 'annee_scolaire', 'semestre', 'actif', 'commentaire'
        ]
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'professeur': forms.Select(attrs={'class': 'form-control'}),
            'salle': forms.Select(attrs={'class': 'form-control'}),
            'creneau': forms.Select(attrs={'class': 'form-control'}),
            'type_cours': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control'}),
            'semestre': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les salles actives
        self.fields['salle'].queryset = Salle.objects.filter(active=True)
        # Filtrer les créneaux non-pause
        self.fields['creneau'].queryset = Creneau.objects.filter(pause=False)
    
    def clean(self):
        cleaned_data = super().clean()
        classe = cleaned_data.get('classe')
        matiere = cleaned_data.get('matiere')
        professeur = cleaned_data.get('professeur')
        annee_scolaire = cleaned_data.get('annee_scolaire')
        semestre = cleaned_data.get('semestre')
        
        # Vérifier qu'une matière n'est pas déjà assignée à un autre professeur dans la même classe
        if classe and matiere and annee_scolaire and semestre:
            from .models import EmploiDuTemps
            
            existing_emploi = EmploiDuTemps.objects.filter(
                classe=classe,
                matiere=matiere,
                annee_scolaire=annee_scolaire,
                semestre=semestre
            )
            
            # Exclure l'instance actuelle si on est en mode édition
            if self.instance.pk:
                existing_emploi = existing_emploi.exclude(pk=self.instance.pk)
            
            if existing_emploi.exists():
                existing_prof = existing_emploi.first().professeur
                raise forms.ValidationError(
                    f"La matière '{matiere.nom}' est déjà assignée au professeur "
                    f"{existing_prof.civilite} {existing_prof.user.last_name} "
                    f"dans la classe {classe.nom} pour l'année {annee_scolaire} "
                    f"semestre {semestre}."
                )
        
        return cleaned_data


class EvenementCalendrierForm(forms.ModelForm):
    class Meta:
        model = EvenementCalendrier
        fields = [
            'titre', 'description', 'type_evenement', 'priorite',
            'date_debut', 'date_fin', 'jour_entier', 'annee_scolaire',
            'classes_concernees', 'professeurs_concernees', 'lieu', 'couleur', 'actif'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'type_evenement': forms.Select(attrs={'class': 'form-control'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'jour_entier': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'annee_scolaire': forms.TextInput(attrs={'class': 'form-control'}),
            'classes_concernees': forms.SelectMultiple(attrs={
                'class': 'form-control select-multiple',
                'size': '8',
                'multiple': True,
                'data-placeholder': 'Sélectionnez les classes concernées...'
            }),
            'professeurs_concernees': forms.SelectMultiple(attrs={
                'class': 'form-control select-multiple',
                'size': '8',
                'multiple': True,
                'data-placeholder': 'Sélectionnez les professeurs concernés...'
            }),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
            'couleur': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            if date_debut >= date_fin:
                raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
        
        return cleaned_data


class ReservationSalleForm(forms.ModelForm):
    class Meta:
        model = ReservationSalle
        fields = [
            'salle', 'titre', 'description', 'date_debut', 'date_fin',
            'motif', 'nombre_personnes', 'equipements_demandes'
        ]
        widgets = {
            'salle': forms.Select(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_debut': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'motif': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_personnes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'equipements_demandes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les salles actives
        self.fields['salle'].queryset = Salle.objects.filter(active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        salle = cleaned_data.get('salle')
        
        if date_debut and date_fin:
            if date_debut >= date_fin:
                raise forms.ValidationError("L'heure de fin doit être postérieure à l'heure de début.")
            
            # Vérifier les conflits de réservation
            if salle:
                conflits = ReservationSalle.objects.filter(
                    salle=salle,
                    statut='CONFIRME',
                    date_debut__lt=date_fin,
                    date_fin__gt=date_debut
                )
                if self.instance.pk:
                    conflits = conflits.exclude(pk=self.instance.pk)
                
                if conflits.exists():
                    raise forms.ValidationError(
                        f"Cette salle est déjà réservée pendant cette période. "
                        f"Conflit avec: {', '.join([r.titre for r in conflits])}"
                    )
        
        return cleaned_data


class ValidationReservationForm(forms.ModelForm):
    """Formulaire pour valider/refuser une réservation"""
    class Meta:
        model = ReservationSalle
        fields = ['statut', 'commentaire_validation']
        widgets = {
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'commentaire_validation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ===== FORMULAIRES DE GESTION DES UTILISATEURS =====

class CustomUserCreationForm(UserCreationForm):
    """Formulaire personnalisé pour créer un utilisateur"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    is_staff = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    is_superuser = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """Formulaire personnalisé pour modifier un utilisateur"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EleveUserForm(forms.ModelForm):
    """Formulaire pour créer/modifier un élève avec compte utilisateur"""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    
    class Meta:
        model = Eleve
        fields = [
            'nom', 'prenom', 'date_naissance', 'lieu_naissance', 'sexe', 'nationalite',
            'numero_etudiant', 'classe', 'adresse', 'telephone', 'email',
            'nom_pere', 'telephone_pere', 'profession_pere',
            'nom_mere', 'telephone_mere', 'profession_mere', 'photo'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_etudiant': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nom_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'profession_pere': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_mere': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_mere': forms.TextInput(attrs={'class': 'form-control'}),
            'profession_mere': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['password'].required = False
            self.fields['password'].help_text = "Laissez vide pour conserver le mot de passe actuel"
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if self.user and self.user.username == username:
            return username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username
    
    def save(self, commit=True):
        eleve = super().save(commit=False)
        
        if self.user:
            # Modification d'un utilisateur existant
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if self.cleaned_data['password']:
                self.user.set_password(self.cleaned_data['password'])
            if commit:
                self.user.save()
                eleve.user = self.user
                eleve.save()
        else:
            # Création d'un nouvel utilisateur
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data['password'] or 'password123'  # Mot de passe par défaut
            )
            if commit:
                eleve.user = user
                eleve.save()
        
        return eleve


class ProfesseurUserForm(forms.ModelForm):
    """Formulaire pour créer/modifier un professeur avec compte utilisateur"""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    
    class Meta:
        model = Professeur
        fields = [
            'civilite', 'telephone', 'adresse', 'date_embauche', 'photo'
        ]
        widgets = {
            'civilite': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_embauche': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['password'].required = False
            self.fields['password'].help_text = "Laissez vide pour conserver le mot de passe actuel"
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if self.user and self.user.username == username:
            return username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username
    
    def save(self, commit=True):
        professeur = super().save(commit=False)
        
        if self.user:
            # Modification d'un utilisateur existant
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if self.cleaned_data['password']:
                self.user.set_password(self.cleaned_data['password'])
            if commit:
                self.user.save()
                professeur.user = self.user
                professeur.save()
        else:
            # Création d'un nouvel utilisateur
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data['password'] or 'password123'  # Mot de passe par défaut
            )
            if commit:
                professeur.user = user
                professeur.save()
        
        return professeur


class ParentUserForm(forms.ModelForm):
    """Formulaire pour créer/modifier un parent avec compte utilisateur"""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    
    class Meta:
        model = Parent
        fields = [
            'nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance', 'nationalite',
            'profession', 'telephone', 'email', 'adresse', 'relation', 'photo'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'relation': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['password'].required = False
            self.fields['password'].help_text = "Laissez vide pour conserver le mot de passe actuel"
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if self.user and self.user.username == username:
            return username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username
    
    def save(self, commit=True):
        parent = super().save(commit=False)
        
        if self.user:
            # Modification d'un utilisateur existant
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if self.cleaned_data['password']:
                self.user.set_password(self.cleaned_data['password'])
            if commit:
                self.user.save()
                parent.user = self.user
                parent.save()
        else:
            # Création d'un nouvel utilisateur
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data['password'] or 'password123'  # Mot de passe par défaut
            )
            if commit:
                parent.user = user
                parent.save()
        
        return parent


class UserProfileForm(forms.ModelForm):
    """Formulaire pour modifier le profil utilisateur"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class PasswordChangeForm(forms.Form):
    """Formulaire pour changer le mot de passe"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Mot de passe actuel'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Nouveau mot de passe'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirmer le nouveau mot de passe'
    )
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Le mot de passe actuel est incorrect.')
        return old_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError('Les nouveaux mots de passe ne correspondent pas.')
            if len(new_password1) < 8:
                raise forms.ValidationError('Le nouveau mot de passe doit contenir au moins 8 caractères.')
        
        return cleaned_data


# =============== FORMULAIRES POUR LA MESSAGERIE ===============

class ConversationForm(forms.ModelForm):
    """Formulaire pour créer une nouvelle conversation"""
    class Meta:
        model = Conversation
        fields = ['titre', 'type_conversation', 'classe']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de la conversation'
            }),
            'type_conversation': forms.Select(attrs={
                'class': 'form-control'
            }),
            'classe': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les classes selon le type d'utilisateur
        if user and hasattr(user, 'professeur'):
            # Professeur : peut créer des conversations pour ses classes
            self.fields['classe'].queryset = Classe.objects.filter(
                professeurs=user.professeur
            )
        elif user and hasattr(user, 'eleve'):
            # Élève : peut créer des conversations pour sa classe
            self.fields['classe'].queryset = Classe.objects.filter(
                id=user.eleve.classe.id
            )
        elif user and hasattr(user, 'parent'):
            # Parent : peut créer des conversations pour les classes de ses enfants
            try:
                parent_instance = user.parent
                enfants_classes = Classe.objects.filter(
                    eleves__parents=parent_instance
                ).distinct()
                self.fields['classe'].queryset = enfants_classes
            except:
                # Si pas d'instance Parent, pas de classes disponibles
                self.fields['classe'].queryset = Classe.objects.none()
        else:
            # Admin : peut créer des conversations pour toutes les classes
            self.fields['classe'].queryset = Classe.objects.all()


class MessageForm(forms.ModelForm):
    """Formulaire pour envoyer un message"""
    class Meta:
        model = Message
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tapez votre message...',
                'style': 'resize: vertical;'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenu'].required = True


class ParticipantForm(forms.Form):
    """Formulaire pour ajouter des participants à une conversation"""
    user = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input participant-checkbox'
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        conversation = kwargs.pop('conversation', None)
        super().__init__(*args, **kwargs)
        
        if conversation and conversation.pk:
            # Récupérer les participants existants
            existing_participants = conversation.participants.values_list('user_id', flat=True)
            
            # Filtrer les utilisateurs selon le type de conversation
            if conversation.type_conversation == 'PROF_PROF':
                # Seuls les professeurs
                self.fields['user'].queryset = User.objects.filter(
                    professeur__isnull=False
                ).exclude(id__in=existing_participants)
            elif conversation.type_conversation == 'PROF_PARENT':
                # Professeurs et parents
                self.fields['user'].queryset = User.objects.filter(
                    models.Q(professeur__isnull=False) | models.Q(parent__isnull=False)
                ).exclude(id__in=existing_participants)
            elif conversation.type_conversation == 'ELEVE_ELEVE':
                # Seuls les élèves
                self.fields['user'].queryset = User.objects.filter(
                    eleve__isnull=False
                ).exclude(id__in=existing_participants)
            elif conversation.type_conversation == 'CLASSE_PROF':
                # Élèves de la classe et professeurs
                if conversation.classe:
                    self.fields['user'].queryset = User.objects.filter(
                        models.Q(eleve__classe=conversation.classe) | 
                        models.Q(professeur__classes=conversation.classe)
                    ).exclude(id__in=existing_participants)
        else:
            # Si pas de conversation ou conversation non sauvegardée, afficher tous les utilisateurs
            self.fields['user'].queryset = User.objects.all()
