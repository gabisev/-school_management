from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import parent_views
from . import bulletin_views
from . import admin_views
from . import planning_views
from . import messaging_views

app_name = 'school_management'

urlpatterns = [
    # Page d'accueil et dashboard
    path('', views.dashboard, name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Tableaux de bord spécialisés
    path('eleve/dashboard/', views.eleve_dashboard, name='eleve_dashboard'),
    path('professeur/dashboard/', views.professeur_dashboard, name='professeur_dashboard'),
    path('parent/dashboard/', parent_views.parent_dashboard, name='parent_dashboard'),
    
    # Gestion des élèves
    path('eleves/', views.EleveListView.as_view(), name='eleve_list'),
    path('eleves/ajouter/', views.EleveCreateView.as_view(), name='eleve_create'),
    path('eleves/<int:pk>/', views.EleveDetailView.as_view(), name='eleve_detail'),
    path('eleves/<int:pk>/modifier/', views.EleveUpdateView.as_view(), name='eleve_update'),
    path('eleves/<int:pk>/supprimer/', views.EleveDeleteView.as_view(), name='eleve_delete'),
    
    # Gestion des professeurs
    path('professeurs/', views.ProfesseurListView.as_view(), name='professeur_list'),
    path('professeurs/ajouter/', views.ProfesseurCreateView.as_view(), name='professeur_create'),
    path('professeurs/<int:pk>/', views.ProfesseurDetailView.as_view(), name='professeur_detail'),
    path('professeurs/<int:pk>/modifier/', views.ProfesseurUpdateView.as_view(), name='professeur_update'),
    path('professeurs/<int:pk>/supprimer/', views.ProfesseurDeleteView.as_view(), name='professeur_delete'),
    
    # Gestion des classes
    path('classes/', views.ClasseListView.as_view(), name='classe_list'),
    path('classes/ajouter/', views.ClasseCreateView.as_view(), name='classe_create'),
    path('classes/<int:pk>/', views.ClasseDetailView.as_view(), name='classe_detail'),
    path('classes/<int:pk>/modifier/', views.ClasseUpdateView.as_view(), name='classe_update'),
    path('classes/<int:pk>/supprimer/', views.ClasseDeleteView.as_view(), name='classe_delete'),
    
    # Gestion des matières
    path('matieres/', views.MatiereListView.as_view(), name='matiere_list'),
    path('matieres/ajouter/', views.MatiereCreateView.as_view(), name='matiere_create'),
    path('matieres/<int:pk>/', views.MatiereDetailView.as_view(), name='matiere_detail'),
    path('matieres/<int:pk>/modifier/', views.MatiereUpdateView.as_view(), name='matiere_update'),
    path('matieres/<int:pk>/supprimer/', views.MatiereDeleteView.as_view(), name='matiere_delete'),
    
    # Gestion des évaluations
    path('evaluations/', views.EvaluationListView.as_view(), name='evaluation_list'),
    path('evaluations/ajouter/', views.EvaluationCreateView.as_view(), name='evaluation_create'),
    path('evaluations/<int:pk>/', views.EvaluationDetailView.as_view(), name='evaluation_detail'),
    path('evaluations/<int:pk>/modifier/', views.EvaluationUpdateView.as_view(), name='evaluation_update'),
    path('evaluations/<int:pk>/supprimer/', views.EvaluationDeleteView.as_view(), name='evaluation_delete'),
    path('evaluations/<int:pk>/notes/', views.saisir_notes, name='saisir_notes'),
    
    # Gestion des notes
    path('notes/', views.NoteListView.as_view(), name='note_list'),
    path('notes/eleve/<int:eleve_id>/', views.notes_eleve, name='notes_eleve'),
    
    # Gestion des absences
    path('absences/', views.AbsenceListView.as_view(), name='absence_list'),
    path('absences/ajouter/', views.AbsenceCreateView.as_view(), name='absence_create'),
    path('absences/<int:pk>/', views.AbsenceDetailView.as_view(), name='absence_detail'),
    path('absences/<int:pk>/modifier/', views.AbsenceUpdateView.as_view(), name='absence_update'),
    path('absences/<int:pk>/supprimer/', views.AbsenceDeleteView.as_view(), name='absence_delete'),
    
    # Rapports
    path('rapports/', views.rapports, name='rapports'),
    path('rapports/classe/<int:classe_id>/', views.rapport_classe, name='rapport_classe'),
    path('rapports/eleve/<int:eleve_id>/', views.bulletin_eleve, name='bulletin_eleve'),
    
    # Logs d'audit (réservé aux administrateurs)
    path('audit/logs/', views.audit_logs, name='audit_logs'),
    
    # Gestion des parents
    path('parents/', views.ParentListView.as_view(), name='parent_list'),
    path('parents/ajouter/', views.ParentCreateView.as_view(), name='parent_create'),
    path('parents/<int:pk>/', views.ParentDetailView.as_view(), name='parent_detail'),
    path('parents/<int:pk>/modifier/', views.ParentUpdateView.as_view(), name='parent_update'),
    path('parents/<int:pk>/supprimer/', views.ParentDeleteView.as_view(), name='parent_delete'),
    
    # Communications
    path('communications/', views.CommunicationListView.as_view(), name='communication_list'),
    path('communications/ajouter/', views.CommunicationCreateView.as_view(), name='communication_create'),
    path('communications/<int:pk>/', views.CommunicationDetailView.as_view(), name='communication_detail'),
    path('communications/<int:pk>/modifier/', views.CommunicationUpdateView.as_view(), name='communication_update'),
    
    # Gestion des profils utilisateur
    path('profil/', views.user_profile, name='user_profile'),
    path('profil/changer-mot-de-passe/', views.change_password, name='change_password'),
    
    # Génération de bulletins
    path('bulletins/generer/<int:eleve_id>/', views.generate_bulletin, name='generate_bulletin'),
    
    # Statistiques d'absences
    path('statistiques/absences/', views.absence_statistics, name='absence_statistics'),
    
    # Analyse des résultats
    path('statistiques/resultats/', views.results_analysis, name='results_analysis'),
    
    # Fonctionnalités d'administration
    path('administration/export-utilisateurs/', views.export_user_data, name='export_user_data'),
    path('administration/synchroniser-comptes/', views.sync_user_accounts, name='sync_user_accounts'),
    path('communications/<int:pk>/supprimer/', views.CommunicationDeleteView.as_view(), name='communication_delete'),
    
    # Vues spécifiques aux parents
    path('parent/enfant/<int:eleve_id>/', parent_views.parent_enfant_detail, name='parent_enfant_detail'),
    path('parent/notes/', parent_views.parent_notes, name='parent_notes'),
    path('parent/absences/', parent_views.parent_absences, name='parent_absences'),
    
    # Bulletins - Vues pour élèves et parents
    path('bulletins/', bulletin_views.BulletinListView.as_view(), name='bulletin_list'),
    path('bulletins/<int:pk>/', bulletin_views.BulletinDetailView.as_view(), name='bulletin_detail'),
    
    # Bulletins - Vues pour professeurs
    path('professeur/bulletins/', bulletin_views.BulletinProfListView.as_view(), name='bulletin_prof_list'),
    path('professeur/bulletins/<int:pk>/', bulletin_views.BulletinProfDetailView.as_view(), name='bulletin_prof_detail'),
    path('professeur/bulletins/<int:pk>/modifier/', bulletin_views.BulletinUpdateView.as_view(), name='bulletin_update'),
    
    # Bulletins - Vues pour professeurs principaux
    path('professeur-principal/bulletins/', bulletin_views.prof_principal_bulletins, name='prof_principal_bulletins'),
    path('professeur-principal/bulletins/classe/<int:classe_id>/trimestre/<int:trimestre>/generer/', bulletin_views.generer_bulletins_classe, name='generer_bulletins_classe'),
    path('professeur-principal/bulletins/classe/<int:classe_id>/trimestre/<int:trimestre>/publier/', bulletin_views.publier_bulletins_classe, name='publier_bulletins_classe'),
    path('bulletins/<int:bulletin_id>/detaille/', bulletin_views.bulletin_detaille_view, name='bulletin_detaille'),
    path('bulletins/<int:bulletin_id>/publier/', bulletin_views.publier_bulletin, name='publier_bulletin'),
    path('mes-bulletins/', bulletin_views.mes_bulletins, name='mes_bulletins'),
    
    # Actions AJAX pour les bulletins
    path('ajax/bulletins/<int:pk>/valider/', bulletin_views.valider_bulletin, name='bulletin_valider'),
    path('ajax/bulletins/eleve/<int:eleve_id>/trimestre/<int:trimestre>/generer/', bulletin_views.generer_bulletin_eleve, name='bulletin_generer_eleve'),
    
    # Administration personnalisée
    path('administration/dashboard/', admin_views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('administration/statistics/', admin_views.admin_statistics, name='admin_statistics'),
    path('administration/users/', admin_views.admin_users_management, name='admin_users'),
    path('administration/professeurs-principaux/', admin_views.admin_prof_principal_management, name='admin_prof_principal'),
    
    # Gestion des utilisateurs
    path('administration/user-management/', admin_views.admin_user_management, name='admin_user_management'),
    path('administration/users/create/', admin_views.admin_create_user, name='admin_create_user'),
    path('administration/users/<int:user_id>/edit/', admin_views.admin_edit_user, name='admin_edit_user'),
    path('administration/users-without-accounts/', admin_views.admin_users_without_accounts, name='admin_users_without_accounts'),
    
    # Gestion des élèves avec comptes
    path('administration/eleves/<int:eleve_id>/create-user/', admin_views.admin_create_eleve_user, name='admin_create_eleve_user'),
    path('administration/eleves/<int:eleve_id>/edit-user/', admin_views.admin_edit_eleve_user, name='admin_edit_eleve_user'),
    
    # Gestion des professeurs avec comptes
    path('administration/professeurs/<int:professeur_id>/create-user/', admin_views.admin_create_professeur_user, name='admin_create_professeur_user'),
    path('administration/professeurs/<int:professeur_id>/edit-user/', admin_views.admin_edit_professeur_user, name='admin_edit_professeur_user'),
    
    # Gestion des parents avec comptes
    path('administration/parents/<int:parent_id>/create-user/', admin_views.admin_create_parent_user, name='admin_create_parent_user'),
    path('administration/parents/<int:parent_id>/edit-user/', admin_views.admin_edit_parent_user, name='admin_edit_parent_user'),
    
    # Gestion des mots de passe et détails utilisateurs
    path('administration/users/<int:user_id>/details/', admin_views.admin_user_details, name='admin_user_details'),
    path('administration/users/<int:user_id>/reset-password/', admin_views.admin_reset_user_password, name='admin_reset_user_password'),
    
    # =============== PLANNINGS ===============
    
    # Tableau de bord du planning
    path('planning/', planning_views.planning_dashboard, name='planning_dashboard'),
    
    # Gestion des salles
    path('planning/salles/', planning_views.SalleListView.as_view(), name='salle_list'),
    path('planning/salles/ajouter/', planning_views.SalleCreateView.as_view(), name='salle_create'),
    path('planning/salles/<int:pk>/', planning_views.SalleDetailView.as_view(), name='salle_detail'),
    path('planning/salles/<int:pk>/modifier/', planning_views.SalleUpdateView.as_view(), name='salle_update'),
    path('planning/salles/<int:pk>/supprimer/', planning_views.SalleDeleteView.as_view(), name='salle_delete'),
    
    # Gestion des créneaux
    path('planning/creneaux/', planning_views.CreneauListView.as_view(), name='creneau_list'),
    path('planning/creneaux/ajouter/', planning_views.CreneauCreateView.as_view(), name='creneau_create'),
    path('planning/creneaux/<int:pk>/modifier/', planning_views.CreneauUpdateView.as_view(), name='creneau_update'),
    path('planning/creneaux/<int:pk>/supprimer/', planning_views.CreneauDeleteView.as_view(), name='creneau_delete'),
    
    # Gestion des emplois du temps
    path('planning/emplois/', planning_views.EmploiDuTempsListView.as_view(), name='emploi_list'),
    path('planning/emplois/ajouter/', planning_views.EmploiDuTempsCreateView.as_view(), name='emploi_create'),
    path('planning/emplois/<int:pk>/', planning_views.EmploiDuTempsDetailView.as_view(), name='emploi_detail'),
    path('planning/emplois/<int:pk>/modifier/', planning_views.EmploiDuTempsUpdateView.as_view(), name='emploi_update'),
    path('planning/emplois/<int:pk>/supprimer/', planning_views.EmploiDuTempsDeleteView.as_view(), name='emploi_delete'),
    path('planning/emplois/classe/<int:classe_id>/', planning_views.emploi_du_temps_classe, name='emploi_classe'),
    path('planning/emplois/professeur/<int:professeur_id>/', planning_views.emploi_du_temps_professeur, name='emploi_professeur'),
    path('planning/mon-emploi/', planning_views.emploi_du_temps_eleve, name='emploi_eleve'),
    
    # Gestion du calendrier
    path('planning/calendrier/', planning_views.calendrier_view, name='calendrier'),
    path('planning/evenements/', planning_views.EvenementCalendrierListView.as_view(), name='evenement_list'),
    path('planning/evenements/ajouter/', planning_views.EvenementCalendrierCreateView.as_view(), name='evenement_create'),
    path('planning/evenements/<int:pk>/', planning_views.EvenementCalendrierDetailView.as_view(), name='evenement_detail'),
    path('planning/evenements/<int:pk>/modifier/', planning_views.EvenementCalendrierUpdateView.as_view(), name='evenement_update'),
    path('planning/evenements/<int:pk>/supprimer/', planning_views.EvenementCalendrierDeleteView.as_view(), name='evenement_delete'),
    
    # Gestion des réservations
    path('planning/reservations/', planning_views.ReservationSalleListView.as_view(), name='reservation_list'),
    path('planning/reservations/ajouter/', planning_views.ReservationSalleCreateView.as_view(), name='reservation_create'),
    path('planning/reservations/<int:pk>/', planning_views.ReservationSalleDetailView.as_view(), name='reservation_detail'),
    path('planning/reservations/<int:pk>/modifier/', planning_views.ReservationSalleUpdateView.as_view(), name='reservation_update'),
    path('planning/reservations/<int:pk>/supprimer/', planning_views.ReservationSalleDeleteView.as_view(), name='reservation_delete'),
    path('planning/reservations/<int:pk>/valider/', planning_views.valider_reservation, name='reservation_valider'),
    
    # Actions AJAX
    path('ajax/salles-disponibles/', planning_views.get_salles_disponibles, name='salles_disponibles'),
    path('ajax/conflits-emploi/', planning_views.get_conflits_emploi, name='conflits_emploi'),
    
    # =============== MESSAGERIE ===============
    path('messagerie/', messaging_views.messaging_dashboard, name='messaging_dashboard'),
    path('messagerie/conversations/', messaging_views.ConversationListView.as_view(), name='conversation_list'),
    path('messagerie/conversations/nouvelle/', messaging_views.ConversationCreateView.as_view(), name='conversation_create'),
    path('messagerie/conversations/<int:pk>/', messaging_views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('messagerie/conversations/<int:pk>/modifier/', messaging_views.ConversationUpdateView.as_view(), name='conversation_update'),
    path('messagerie/conversations/<int:conversation_id>/envoyer-message/', messaging_views.send_message, name='send_message'),
    path('messagerie/conversations/<int:conversation_id>/ajouter-participants/', messaging_views.add_participants, name='add_participants'),
    path('messagerie/conversations/<int:conversation_id>/retirer-participant/<int:user_id>/', messaging_views.remove_participant, name='remove_participant'),
    path('ajax/messagerie/conversations/<int:conversation_id>/messages/', messaging_views.get_conversation_messages, name='get_conversation_messages'),
]
