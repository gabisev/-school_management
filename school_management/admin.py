from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Classe, Matiere, Professeur, Eleve, 
    Evaluation, Note, Absence, AnneeScolaire
)


@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ['annee', 'date_debut', 'date_fin', 'active']
    list_filter = ['active']
    search_fields = ['annee']


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'niveau', 'annee_scolaire', 'effectif_actuel', 'effectif_max']
    list_filter = ['niveau', 'annee_scolaire']
    search_fields = ['nom', 'niveau']
    ordering = ['niveau', 'nom']


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'coefficient']
    search_fields = ['nom', 'code']
    ordering = ['nom']


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'civilite', 'telephone', 'date_embauche']
    list_filter = ['civilite', 'date_embauche', 'matieres']
    search_fields = ['user__last_name', 'user__first_name', 'telephone']
    filter_horizontal = ['matieres', 'classes']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('user', 'civilite', 'photo')
        }),
        ('Contact', {
            'fields': ('telephone', 'adresse')
        }),
        ('Informations professionnelles', {
            'fields': ('date_embauche', 'matieres', 'classes')
        }),
    )


@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'numero_etudiant', 'classe', 'age', 'statut']
    list_filter = ['classe', 'sexe', 'statut', 'date_inscription']
    search_fields = ['nom', 'prenom', 'numero_etudiant']
    ordering = ['nom', 'prenom']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'date_naissance', 'lieu_naissance', 
                      'sexe', 'nationalite', 'photo')
        }),
        ('Informations scolaires', {
            'fields': ('numero_etudiant', 'classe', 'statut')
        }),
        ('Contact', {
            'fields': ('adresse', 'telephone', 'email')
        }),
        ('Informations parents', {
            'fields': ('nom_pere', 'telephone_pere', 'profession_pere',
                      'nom_mere', 'telephone_mere', 'profession_mere'),
            'classes': ['collapse']
        }),
    )


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    fields = ['eleve', 'note', 'absent', 'commentaire']


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'matiere', 'classe', 'professeur', 'date_evaluation', 'type_evaluation']
    list_filter = ['matiere', 'classe', 'type_evaluation', 'date_evaluation']
    search_fields = ['titre', 'description']
    date_hierarchy = 'date_evaluation'
    inlines = [NoteInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'type_evaluation')
        }),
        ('Paramètres', {
            'fields': ('matiere', 'classe', 'professeur', 'date_evaluation')
        }),
        ('Notation', {
            'fields': ('note_sur', 'coefficient')
        }),
    )


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'evaluation', 'note', 'absent', 'date_saisie']
    list_filter = ['evaluation__matiere', 'evaluation__classe', 'absent', 'date_saisie']
    search_fields = ['eleve__nom', 'eleve__prenom', 'evaluation__titre']
    date_hierarchy = 'date_saisie'


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'date_debut', 'date_fin', 'motif', 'justifiee']
    list_filter = ['motif', 'justifiee', 'date_debut']
    search_fields = ['eleve__nom', 'eleve__prenom']
    date_hierarchy = 'date_debut'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('eleve', 'date_debut', 'date_fin')
        }),
        ('Justification', {
            'fields': ('motif', 'justifiee', 'commentaire', 'document_justificatif')
        }),
    )


# Personnalisation de l'admin
admin.site.site_header = "Administration École"
admin.site.site_title = "École Admin"
admin.site.index_title = "Panneau d'administration de l'école"
