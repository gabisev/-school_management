from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone


class Classe(models.Model):
    """Modèle pour représenter une classe"""
    nom = models.CharField(max_length=50, unique=True)
    niveau = models.CharField(max_length=20)
    annee_scolaire = models.CharField(max_length=9, default="2024-2025")
    effectif_max = models.PositiveIntegerField(default=30)
    prof_principal = models.ForeignKey('Professeur', on_delete=models.SET_NULL, null=True, blank=True, related_name='classes_principales')
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ['niveau', 'nom']
        constraints = [
            models.UniqueConstraint(
                fields=['prof_principal'],
                condition=models.Q(prof_principal__isnull=False),
                name='unique_prof_principal_per_classe'
            )
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.niveau})"
    
    def get_absolute_url(self):
        return reverse('school_management:classe_detail', kwargs={'pk': self.pk})
    
    @property
    def effectif_actuel(self):
        return self.eleves.count()
    
    def clean(self):
        """Validation personnalisée du modèle"""
        from django.core.exceptions import ValidationError
        
        # Vérifier qu'un professeur n'est pas déjà principal d'une autre classe
        if self.prof_principal:
            existing_classe = Classe.objects.filter(
                prof_principal=self.prof_principal
            ).exclude(pk=self.pk)
            
            if existing_classe.exists():
                existing_classe_nom = existing_classe.first().nom
                raise ValidationError(
                    f"Le professeur {self.prof_principal.civilite} {self.prof_principal.user.last_name} "
                    f"est déjà professeur principal de la classe {existing_classe_nom}. "
                    f"Un professeur ne peut être principal que d'une seule classe."
                )


class Matiere(models.Model):
    """Modèle pour représenter une matière"""
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    coefficient = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
    
    def get_absolute_url(self):
        return reverse('school_management:matiere_detail', kwargs={'pk': self.pk})


class Professeur(models.Model):
    """Modèle pour représenter un professeur"""
    CIVILITE_CHOICES = [
        ('M', 'Monsieur'),
        ('Mme', 'Madame'),
        ('Mlle', 'Mademoiselle'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    civilite = models.CharField(max_length=4, choices=CIVILITE_CHOICES)
    telephone = models.CharField(max_length=15, blank=True)
    adresse = models.TextField(blank=True)
    date_embauche = models.DateField()
    matieres = models.ManyToManyField(Matiere, related_name='professeurs')
    classes = models.ManyToManyField(Classe, related_name='professeurs', blank=True)
    photo = models.ImageField(upload_to='professeurs/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Professeur"
        verbose_name_plural = "Professeurs"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.civilite} {self.user.last_name} {self.user.first_name}"
    
    def get_absolute_url(self):
        return reverse('school_management:professeur_detail', kwargs={'pk': self.pk})
    
    @property
    def nom_complet(self):
        return f"{self.user.last_name} {self.user.first_name}"


class Eleve(models.Model):
    """Modèle pour représenter un élève"""
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    # Liaison avec le système d'authentification Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Informations personnelles
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    nationalite = models.CharField(max_length=50, default="Française")
    
    # Informations scolaires
    numero_etudiant = models.CharField(max_length=20, unique=True)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='eleves')
    date_inscription = models.DateField(auto_now_add=True)
    
    # Informations de contact
    adresse = models.TextField()
    telephone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    
    # Informations des parents/tuteurs
    nom_pere = models.CharField(max_length=100, blank=True)
    telephone_pere = models.CharField(max_length=15, blank=True)
    profession_pere = models.CharField(max_length=100, blank=True)
    
    nom_mere = models.CharField(max_length=100, blank=True)
    telephone_mere = models.CharField(max_length=15, blank=True)
    profession_mere = models.CharField(max_length=100, blank=True)
    
    # Relation avec les parents (nouveau système)
    parents = models.ManyToManyField('Parent', related_name='eleves', blank=True)
    
    # Autres informations
    photo = models.ImageField(upload_to='eleves/', blank=True, null=True)
    statut = models.BooleanField(default=True, help_text="Actif/Inactif")
    
    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        if self.user:
            return f"{self.user.last_name} {self.user.first_name}"
        return f"{self.nom} {self.prenom}"
    
    def get_absolute_url(self):
        return reverse('school_management:eleve_detail', kwargs={'pk': self.pk})
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))


class Evaluation(models.Model):
    """Modèle pour représenter une évaluation"""
    TYPE_CHOICES = [
        ('DS', 'Devoir Surveillé'),
        ('DM', 'Devoir Maison'),
        ('CC', 'Contrôle Continu'),
        ('EX', 'Examen'),
        ('TP', 'Travaux Pratiques'),
        ('OR', 'Oral'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='evaluations')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='evaluations')
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE, related_name='evaluations')
    date_evaluation = models.DateTimeField()
    type_evaluation = models.CharField(max_length=2, choices=TYPE_CHOICES)
    note_sur = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    coefficient = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    trimestre = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], default=1)
    annee_scolaire = models.CharField(max_length=9, default="2024-2025")
    
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-date_evaluation']
    
    def __str__(self):
        return f"{self.titre} - {self.matiere.nom} ({self.classe.nom})"
    
    def get_absolute_url(self):
        return reverse('school_management:evaluation_detail', kwargs={'pk': self.pk})


class Note(models.Model):
    """Modèle pour représenter une note"""
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='notes')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='notes')
    note = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True, 
        blank=True
    )
    absent = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True)
    date_saisie = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ['eleve', 'evaluation']
        ordering = ['-date_saisie']
    
    def __str__(self):
        if self.absent:
            return f"{self.eleve.nom_complet} - {self.evaluation.titre} : Absent"
        elif self.note is not None:
            return f"{self.eleve.nom_complet} - {self.evaluation.titre} : {self.note}/{self.evaluation.note_sur}"
        else:
            return f"{self.eleve.nom_complet} - {self.evaluation.titre} : Non noté"
    
    def get_absolute_url(self):
        return reverse('school_management:note_list')
    
    @property
    def note_sur_20(self):
        """Convertit la note sur 20"""
        if self.note is not None and self.evaluation.note_sur != 20:
            return (self.note * 20) / self.evaluation.note_sur
        return self.note


class Absence(models.Model):
    """Modèle pour gérer les absences"""
    MOTIF_CHOICES = [
        ('M', 'Maladie'),
        ('F', 'Familial'),
        ('A', 'Autre'),
        ('NJ', 'Non justifiée'),
    ]
    
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='absences')
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    motif = models.CharField(max_length=2, choices=MOTIF_CHOICES)
    justifiee = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True)
    document_justificatif = models.FileField(upload_to='justificatifs/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Absence"
        verbose_name_plural = "Absences"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.eleve.nom_complet} - {self.date_debut.date()}"
    
    def get_absolute_url(self):
        return reverse('school_management:absence_detail', kwargs={'pk': self.pk})
    
    @property
    def duree_en_heures(self):
        """Calcule la durée de l'absence en heures"""
        return (self.date_fin - self.date_debut).total_seconds() / 3600


class AnneeScolaire(models.Model):
    """Modèle pour représenter une année scolaire"""
    annee = models.CharField(max_length=9, unique=True)  # ex: "2024-2025"
    date_debut = models.DateField()
    date_fin = models.DateField()
    active = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Année Scolaire"
        verbose_name_plural = "Années Scolaires"
        ordering = ['-annee']
    
    def __str__(self):
        return self.annee
    
    def save(self, *args, **kwargs):
        if self.active:
            # S'assurer qu'une seule année scolaire est active
            AnneeScolaire.objects.filter(active=True).update(active=False)
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """Modèle pour enregistrer les logs d'activité des utilisateurs"""
    ACTION_CHOICES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VIEW', 'Consultation'),
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('NOTE_SAVE', 'Saisie de notes'),
        ('ABSENCE_CREATE', 'Création d\'absence'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    model_name = models.CharField(max_length=50, verbose_name="Modèle concerné")
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID de l'objet")
    object_repr = models.CharField(max_length=200, verbose_name="Représentation de l'objet")
    details = models.TextField(blank=True, verbose_name="Détails")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date et heure")
    
    class Meta:
        verbose_name = "Log d'audit"
        verbose_name_plural = "Logs d'audit"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.model_name} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    
    def get_user_type(self):
        """Retourne le type d'utilisateur"""
        if self.user.is_superuser or self.user.is_staff:
            return 'admin'
        try:
            if hasattr(self.user, 'eleve'):
                return 'eleve'
        except:
            pass
        try:
            if hasattr(self.user, 'professeur'):
                return 'professeur'
        except:
            pass
        return 'unknown'


class Parent(models.Model):
    """Modèle pour représenter un parent d'élève"""
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    RELATION_CHOICES = [
        ('PERE', 'Père'),
        ('MERE', 'Mère'),
        ('TUTEUR', 'Tuteur légal'),
        ('AUTRE', 'Autre'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, blank=True)
    nationalite = models.CharField(max_length=50, default="Française")
    profession = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES, default='PERE')
    photo = models.ImageField(upload_to='parents/', null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        if self.user:
            return f"{self.user.last_name} {self.user.first_name}"
        return f"{self.nom} {self.prenom}"
    
    def get_absolute_url(self):
        return reverse('school_management:parent_detail', kwargs={'pk': self.pk})
    
    def get_enfants(self):
        """Retourne tous les enfants de ce parent"""
        return self.eleves.all()
    
    def get_nom_complet(self):
        """Retourne le nom complet du parent"""
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}"
        return f"{self.prenom} {self.nom}"


class Communication(models.Model):
    """Modèle pour les communications de l'école"""
    TYPE_CHOICES = [
        ('INFO', 'Information générale'),
        ('URGENT', 'Urgent'),
        ('EVENEMENT', 'Événement'),
        ('RAPPEL', 'Rappel'),
        ('CONSEIL', 'Conseil'),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', 'Basse'),
        ('NORMALE', 'Normale'),
        ('HAUTE', 'Haute'),
        ('URGENTE', 'Urgente'),
    ]
    
    DESTINATAIRES_CHOICES = [
        ('TOUS', 'Tous les utilisateurs'),
        ('PARENTS', 'Parents uniquement'),
        ('ELEVES', 'Élèves uniquement'),
        ('PROFESSEURS', 'Professeurs uniquement'),
        ('ADMINS', 'Administrateurs uniquement'),
        ('CLASSE', 'Classe spécifique'),
    ]
    
    titre = models.CharField(max_length=200, verbose_name="Titre")
    contenu = models.TextField(verbose_name="Contenu")
    type_communication = models.CharField(max_length=20, choices=TYPE_CHOICES, default='INFO', verbose_name="Type")
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='NORMALE', verbose_name="Priorité")
    destinataires = models.CharField(max_length=20, choices=DESTINATAIRES_CHOICES, default='TOUS', verbose_name="Destinataires")
    classe_cible = models.ForeignKey(Classe, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Classe cible")
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    date_publication = models.DateTimeField(null=True, blank=True, verbose_name="Date de publication")
    date_expiration = models.DateTimeField(null=True, blank=True, verbose_name="Date d'expiration")
    active = models.BooleanField(default=True, verbose_name="Active")
    piece_jointe = models.FileField(upload_to='communications/', null=True, blank=True, verbose_name="Pièce jointe")
    
    class Meta:
        verbose_name = "Communication"
        verbose_name_plural = "Communications"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.get_type_communication_display()}"
    
    def get_absolute_url(self):
        return reverse('school_management:communication_detail', kwargs={'pk': self.pk})
    
    def is_publiee(self):
        """Vérifie si la communication est publiée"""
        if not self.active:
            return False
        if self.date_publication and self.date_publication > timezone.now():
            return False
        if self.date_expiration and self.date_expiration < timezone.now():
            return False
        return True
    
    def get_destinataires_display_custom(self):
        """Retourne l'affichage personnalisé des destinataires"""
        if self.destinataires == 'CLASSE' and self.classe_cible:
            return f"Classe {self.classe_cible.nom}"
        # Utiliser la méthode Django générée automatiquement
        return self.get_destinataires_display()
    
    def get_priorite_color(self):
        """Retourne la couleur CSS selon la priorité"""
        colors = {
            'BASSE': 'success',
            'NORMALE': 'primary',
            'HAUTE': 'warning',
            'URGENTE': 'danger',
        }
        return colors.get(self.priorite, 'primary')
    
    def get_type_color(self):
        """Retourne la couleur CSS selon le type"""
        colors = {
            'INFO': 'info',
            'URGENT': 'danger',
            'EVENEMENT': 'success',
            'RAPPEL': 'warning',
            'CONSEIL': 'primary',
        }
        return colors.get(self.type_communication, 'primary')


class Bulletin(models.Model):
    """Modèle pour représenter un bulletin de notes"""
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('ARCHIVE', 'Archivé'),
    ]
    
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='bulletins')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='bulletins')
    annee_scolaire = models.CharField(max_length=9, default="2024-2025")
    trimestre = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='BROUILLON')
    
    # Moyennes et appréciations
    moyenne_generale = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    rang = models.PositiveIntegerField(null=True, blank=True)
    appreciation_generale = models.TextField(blank=True)
    appreciation_prof_principal = models.TextField(blank=True)
    
    # Informations sur la classe
    effectif_classe = models.PositiveIntegerField(null=True, blank=True)
    moyenne_classe = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bulletins_crees')
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bulletins_valides')
    
    class Meta:
        verbose_name = "Bulletin"
        verbose_name_plural = "Bulletins"
        unique_together = ['eleve', 'annee_scolaire', 'trimestre']
        ordering = ['-trimestre', 'eleve__user__last_name']
    
    def __str__(self):
        return f"Bulletin {self.trimestre} - {self.eleve.nom_complet} ({self.annee_scolaire})"
    
    def get_absolute_url(self):
        return reverse('school_management:bulletin_detail', kwargs={'pk': self.pk})
    
    def calculer_moyenne_generale(self):
        """Calcule la moyenne générale du bulletin"""
        from django.db.models import Avg, F
        
        # Récupérer toutes les notes de l'élève pour ce trimestre
        notes = Note.objects.filter(
            eleve=self.eleve,
            evaluation__trimestre=self.trimestre,
            evaluation__annee_scolaire=self.annee_scolaire,
            note__isnull=False
        ).select_related('evaluation__matiere')
        
        if not notes.exists():
            return None
        
        # Calculer la moyenne pondérée par coefficient
        total_points = 0
        total_coefficients = 0
        
        for note in notes:
            coefficient = note.evaluation.matiere.coefficient
            note_sur_20 = note.note_sur_20 or 0
            total_points += note_sur_20 * coefficient
            total_coefficients += coefficient
        
        if total_coefficients > 0:
            return round(total_points / total_coefficients, 2)
        return None
    
    def calculer_rang(self):
        """Calcule le rang de l'élève dans sa classe"""
        if not self.moyenne_generale:
            return None
        
        # Compter le nombre d'élèves avec une moyenne supérieure
        bulletins_superieurs = Bulletin.objects.filter(
            classe=self.classe,
            annee_scolaire=self.annee_scolaire,
            trimestre=self.trimestre,
            moyenne_generale__gt=self.moyenne_generale,
            statut__in=['VALIDE', 'EN_ATTENTE']
        ).count()
        
        return bulletins_superieurs + 1
    
    def calculer_moyenne_classe(self):
        """Calcule la moyenne générale de la classe"""
        from django.db.models import Avg
        
        # Récupérer toutes les moyennes générales de la classe pour ce trimestre
        bulletins_classe = Bulletin.objects.filter(
            classe=self.classe,
            annee_scolaire=self.annee_scolaire,
            trimestre=self.trimestre,
            moyenne_generale__isnull=False,
            statut__in=['VALIDE', 'EN_ATTENTE']
        )
        
        if bulletins_classe.exists():
            moyenne = bulletins_classe.aggregate(
                moyenne=Avg('moyenne_generale')
            )['moyenne']
            return round(moyenne, 2) if moyenne else None
        
        return None
    
    def calculer_effectif_classe(self):
        """Calcule l'effectif de la classe"""
        return Bulletin.objects.filter(
            classe=self.classe,
            annee_scolaire=self.annee_scolaire,
            trimestre=self.trimestre,
            statut__in=['VALIDE', 'EN_ATTENTE']
        ).count()
    
    def recalculer_tous_les_champs(self):
        """Recalcule automatiquement tous les champs du bulletin"""
        # Calculer la moyenne générale
        self.moyenne_generale = self.calculer_moyenne_generale()
        
        # Calculer le rang
        self.rang = self.calculer_rang()
        
        # Calculer la moyenne de la classe
        self.moyenne_classe = self.calculer_moyenne_classe()
        
        # Calculer l'effectif de la classe
        self.effectif_classe = self.calculer_effectif_classe()
        
        # Sauvegarder les modifications
        self.save(update_fields=['moyenne_generale', 'rang', 'moyenne_classe', 'effectif_classe'])
        
        return self
    
    def peut_etre_modifie_par(self, user):
        """Vérifie si l'utilisateur peut modifier ce bulletin"""
        if not user.is_authenticated:
            return False
        
        # Seul le professeur principal peut modifier
        if hasattr(user, 'professeur'):
            return self.classe.prof_principal == user.professeur
        
        # Les administrateurs peuvent modifier
        return user.is_staff or user.is_superuser
    
    def est_complet(self):
        """Vérifie si toutes les évaluations sont complétées pour ce trimestre"""
        # Récupérer toutes les matières de la classe
        matieres_classe = self.classe.eleves.first().classe.professeurs.values_list('matieres', flat=True).distinct()
        
        # Vérifier que chaque matière a au moins une évaluation pour ce trimestre
        for matiere_id in matieres_classe:
            evaluations = Evaluation.objects.filter(
                matiere_id=matiere_id,
                trimestre=self.trimestre,
                annee_scolaire=self.annee_scolaire
            )
            
            if not evaluations.exists():
                return False
            
            # Vérifier que l'élève a une note pour chaque évaluation
            for evaluation in evaluations:
                if not Note.objects.filter(
                    eleve=self.eleve,
                    evaluation=evaluation,
                    note__isnull=False
                ).exists():
                    return False
        
        return True


class NoteBulletin(models.Model):
    """Modèle pour les notes détaillées dans un bulletin"""
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, related_name='notes_detaillees')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    moyenne_matiere = models.DecimalField(max_digits=4, decimal_places=2)
    coefficient = models.DecimalField(max_digits=3, decimal_places=1)
    appreciation = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Note de bulletin"
        verbose_name_plural = "Notes de bulletin"
        unique_together = ['bulletin', 'matiere']
        ordering = ['matiere__nom']
    
    def __str__(self):
        return f"{self.bulletin} - {self.matiere.nom}: {self.moyenne_matiere}"


# =============== MODÈLES POUR LES PLANNINGS ===============

class Salle(models.Model):
    """Modèle pour représenter une salle"""
    nom = models.CharField(max_length=50, unique=True)
    numero = models.CharField(max_length=10, unique=True)
    capacite = models.PositiveIntegerField(default=30)
    type_salle = models.CharField(max_length=20, choices=[
        ('COURS', 'Salle de cours'),
        ('LABO', 'Laboratoire'),
        ('INFO', 'Salle informatique'),
        ('SPORT', 'Salle de sport'),
        ('BIBLIO', 'Bibliothèque'),
        ('AUDITORIUM', 'Auditorium'),
        ('AUTRE', 'Autre'),
    ], default='COURS')
    equipements = models.TextField(blank=True, help_text="Équipements disponibles")
    accessible_handicap = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Salle"
        verbose_name_plural = "Salles"
        ordering = ['numero']
    
    def __str__(self):
        return f"{self.nom} ({self.numero})"
    
    def get_absolute_url(self):
        return reverse('school_management:salle_detail', kwargs={'pk': self.pk})


class Creneau(models.Model):
    """Modèle pour représenter un créneau horaire"""
    JOURS_SEMAINE = [
        ('LUNDI', 'Lundi'),
        ('MARDI', 'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI', 'Samedi'),
    ]
    
    jour = models.CharField(max_length=10, choices=JOURS_SEMAINE)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    duree_minutes = models.PositiveIntegerField(default=55)
    pause = models.BooleanField(default=False, help_text="Créneau de pause")
    
    class Meta:
        verbose_name = "Créneau"
        verbose_name_plural = "Créneaux"
        ordering = ['jour', 'heure_debut']
        unique_together = ['jour', 'heure_debut']
    
    def __str__(self):
        return f"{self.get_jour_display()} {self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')}"
    
    def get_absolute_url(self):
        return reverse('school_management:creneau_detail', kwargs={'pk': self.pk})


class EmploiDuTemps(models.Model):
    """Modèle pour l'emploi du temps"""
    TYPE_COURS = [
        ('COURS', 'Cours normal'),
        ('TD', 'Travaux dirigés'),
        ('TP', 'Travaux pratiques'),
        ('EXAMEN', 'Examen'),
        ('CONTROLE', 'Contrôle'),
        ('REUNION', 'Réunion'),
        ('AUTRE', 'Autre'),
    ]
    
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='emplois_du_temps')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE)
    salle = models.ForeignKey(Salle, on_delete=models.CASCADE)
    creneau = models.ForeignKey(Creneau, on_delete=models.CASCADE)
    type_cours = models.CharField(max_length=20, choices=TYPE_COURS, default='COURS')
    annee_scolaire = models.CharField(max_length=9, default="2024-2025")
    semestre = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)], default=1)
    actif = models.BooleanField(default=True)
    commentaire = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Emploi du temps"
        verbose_name_plural = "Emplois du temps"
        ordering = ['classe', 'creneau__jour', 'creneau__heure_debut']
        unique_together = [
            ['classe', 'creneau', 'annee_scolaire', 'semestre'],
            ['classe', 'matiere', 'annee_scolaire', 'semestre']  # Une matière ne peut être assignée qu'à un seul prof par classe
        ]
    
    def __str__(self):
        return f"{self.classe} - {self.matiere} - {self.creneau}"
    
    def get_absolute_url(self):
        return reverse('school_management:emploi_detail', kwargs={'pk': self.pk})
    
    def clean(self):
        """Validation personnalisée du modèle"""
        from django.core.exceptions import ValidationError
        
        # Vérifier qu'une matière n'est pas déjà assignée à un autre professeur dans la même classe
        if self.classe and self.matiere and self.annee_scolaire and self.semestre:
            existing_emploi = EmploiDuTemps.objects.filter(
                classe=self.classe,
                matiere=self.matiere,
                annee_scolaire=self.annee_scolaire,
                semestre=self.semestre
            ).exclude(pk=self.pk)
            
            if existing_emploi.exists():
                existing_prof = existing_emploi.first().professeur
                raise ValidationError(
                    f"La matière '{self.matiere.nom}' est déjà assignée au professeur "
                    f"{existing_prof.civilite} {existing_prof.user.last_name} "
                    f"dans la classe {self.classe.nom} pour l'année {self.annee_scolaire} "
                    f"semestre {self.semestre}."
                )
    
    def conflit_professeur(self):
        """Vérifie s'il y a un conflit avec un autre cours du professeur"""
        return EmploiDuTemps.objects.filter(
            professeur=self.professeur,
            creneau=self.creneau,
            annee_scolaire=self.annee_scolaire,
            semestre=self.semestre,
            actif=True
        ).exclude(pk=self.pk).exists()
    
    def conflit_salle(self):
        """Vérifie s'il y a un conflit avec une autre utilisation de la salle"""
        return EmploiDuTemps.objects.filter(
            salle=self.salle,
            creneau=self.creneau,
            annee_scolaire=self.annee_scolaire,
            semestre=self.semestre,
            actif=True
        ).exclude(pk=self.pk).exists()
    
    def conflit_classe(self):
        """Vérifie s'il y a un conflit avec un autre cours de la classe"""
        return EmploiDuTemps.objects.filter(
            classe=self.classe,
            creneau=self.creneau,
            annee_scolaire=self.annee_scolaire,
            semestre=self.semestre,
            actif=True
        ).exclude(pk=self.pk).exists()
    
    def a_des_conflits(self):
        """Vérifie s'il y a des conflits"""
        return self.conflit_professeur() or self.conflit_salle() or self.conflit_classe()


class EvenementCalendrier(models.Model):
    """Modèle pour les événements du calendrier scolaire"""
    TYPE_EVENEMENT = [
        ('VACANCES', 'Vacances'),
        ('JOUR_FERIE', 'Jour férié'),
        ('EXAMEN', 'Examen'),
        ('REUNION', 'Réunion'),
        ('SORTIE', 'Sortie scolaire'),
        ('EVENEMENT', 'Événement'),
        ('FORMATION', 'Formation'),
        ('AUTRE', 'Autre'),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', 'Basse'),
        ('NORMALE', 'Normale'),
        ('HAUTE', 'Haute'),
        ('URGENTE', 'Urgente'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type_evenement = models.CharField(max_length=20, choices=TYPE_EVENEMENT)
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='NORMALE')
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    jour_entier = models.BooleanField(default=False)
    annee_scolaire = models.CharField(max_length=9, default="2024-2025")
    classes_concernees = models.ManyToManyField(Classe, blank=True, related_name='evenements')
    professeurs_concernees = models.ManyToManyField(Professeur, blank=True, related_name='evenements')
    lieu = models.CharField(max_length=200, blank=True)
    organisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evenements_organises')
    couleur = models.CharField(max_length=7, default='#007bff', help_text="Couleur hexadécimale")
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Événement calendrier"
        verbose_name_plural = "Événements calendrier"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.date_debut.strftime('%d/%m/%Y')}"
    
    def get_absolute_url(self):
        return reverse('school_management:evenement_detail', kwargs={'pk': self.pk})
    
    def duree_jours(self):
        """Calcule la durée en jours"""
        if self.jour_entier:
            return (self.date_fin.date() - self.date_debut.date()).days + 1
        return 0
    
    def est_en_cours(self):
        """Vérifie si l'événement est en cours"""
        now = timezone.now()
        return self.date_debut <= now <= self.date_fin
    
    def est_passe(self):
        """Vérifie si l'événement est passé"""
        return timezone.now() > self.date_fin
    
    def est_futur(self):
        """Vérifie si l'événement est dans le futur"""
        return timezone.now() < self.date_debut


class ReservationSalle(models.Model):
    """Modèle pour les réservations de salles"""
    STATUT_CHOICES = [
        ('DEMANDE', 'Demande'),
        ('CONFIRME', 'Confirmé'),
        ('REFUSE', 'Refusé'),
        ('ANNULE', 'Annulé'),
    ]
    
    salle = models.ForeignKey(Salle, on_delete=models.CASCADE, related_name='reservations')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='DEMANDE')
    motif = models.CharField(max_length=200, blank=True)
    nombre_personnes = models.PositiveIntegerField(default=1)
    equipements_demandes = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    commentaire_validation = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Réservation de salle"
        verbose_name_plural = "Réservations de salles"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.salle} - {self.titre} ({self.date_debut.strftime('%d/%m/%Y %H:%M')})"
    
    def get_absolute_url(self):
        return reverse('school_management:reservation_detail', kwargs={'pk': self.pk})
    
    def conflit_reservation(self):
        """Vérifie s'il y a un conflit avec une autre réservation"""
        return ReservationSalle.objects.filter(
            salle=self.salle,
            statut='CONFIRME',
            date_debut__lt=self.date_fin,
            date_fin__gt=self.date_debut
        ).exclude(pk=self.pk).exists()
    
    def duree_heures(self):
        """Calcule la durée en heures"""
        delta = self.date_fin - self.date_debut
        return delta.total_seconds() / 3600
    
    def peut_etre_modifiee_par(self, user):
        """Vérifie si l'utilisateur peut modifier cette réservation"""
        if not user.is_authenticated:
            return False
        
        # L'utilisateur qui a créé la réservation peut la modifier
        if self.utilisateur == user:
            return True
        
        # Les administrateurs peuvent modifier
        return user.is_staff or user.is_superuser


# =============== MODÈLES POUR LA MESSAGERIE ===============

class Conversation(models.Model):
    """Modèle pour représenter une conversation de messagerie"""
    TYPE_CHOICES = [
        ('PROF_PROF', 'Entre professeurs'),
        ('PROF_PARENT', 'Professeur - Parent'),
        ('ELEVE_ELEVE', 'Entre élèves'),
        ('CLASSE_PROF', 'Classe avec professeur'),
    ]
    
    titre = models.CharField(max_length=200)
    type_conversation = models.CharField(max_length=20, choices=TYPE_CHOICES)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    createur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_creees', default=1)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-date_modification']
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_conversation_display()})"
    
    def get_absolute_url(self):
        return reverse('school_management:conversation_detail', kwargs={'pk': self.pk})
    
    def get_participants(self):
        """Retourne tous les participants de la conversation"""
        return self.participants.all()
    
    def get_last_message(self):
        """Retourne le dernier message de la conversation"""
        return self.messages.order_by('-date_envoi').first()
    
    def get_unread_count(self, user):
        """Retourne le nombre de messages non lus pour un utilisateur"""
        return self.messages.filter(
            date_envoi__gt=user.last_login or user.date_joined,
            expediteur__user__isnull=False
        ).exclude(expediteur__user=user).count()
    
    def get_type_conversation_color(self):
        """Retourne la couleur Bootstrap correspondant au type de conversation"""
        colors = {
            'PROF_PROF': 'primary',
            'PROF_PARENT': 'success',
            'ELEVE_ELEVE': 'info',
            'CLASSE_PROF': 'warning',
        }
        return colors.get(self.type_conversation, 'secondary')
    
    def est_createur(self, user):
        """Vérifie si l'utilisateur est le créateur de la conversation"""
        return self.createur == user
    
    def peut_gerer_participants(self, user):
        """Vérifie si l'utilisateur peut gérer les participants (créateur uniquement)"""
        return self.est_createur(user)


class Participant(models.Model):
    """Modèle pour représenter un participant dans une conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_participant')
    date_ajout = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"
        unique_together = ['conversation', 'user']
        ordering = ['date_ajout']
    
    def __str__(self):
        return f"{self.user.get_full_name()} dans {self.conversation.titre}"


class Message(models.Model):
    """Modèle pour représenter un message dans une conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    date_lecture = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['date_envoi']
    
    def __str__(self):
        return f"Message de {self.expediteur.get_full_name()} dans {self.conversation.titre}"
    
    def marquer_comme_lu(self):
        """Marque le message comme lu"""
        if not self.lu:
            self.lu = True
            self.date_lecture = timezone.now()
            self.save()
    
    def get_absolute_url(self):
        return reverse('school_management:conversation_detail', kwargs={'pk': self.conversation.pk})
