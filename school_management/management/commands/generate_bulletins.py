from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from school_management.models import (
    Bulletin, NoteBulletin, Eleve, Classe, Matiere, 
    Note, Evaluation, Professeur
)
from django.contrib.auth.models import User
from django.db.models import Avg


class Command(BaseCommand):
    help = 'Génère automatiquement les bulletins pour tous les élèves'

    def add_arguments(self, parser):
        parser.add_argument(
            '--trimestre',
            type=int,
            choices=[1, 2, 3],
            help='Trimestre pour lequel générer les bulletins'
        )
        parser.add_argument(
            '--annee',
            type=str,
            default='2024-2025',
            help='Année scolaire (défaut: 2024-2025)'
        )
        parser.add_argument(
            '--classe',
            type=str,
            help='Nom de la classe spécifique (optionnel)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la régénération même si le bulletin existe déjà'
        )

    def handle(self, *args, **options):
        trimestre = options['trimestre']
        annee_scolaire = options['annee']
        classe_nom = options.get('classe')
        force = options['force']

        if not trimestre:
            self.stdout.write(
                self.style.ERROR('Veuillez spécifier un trimestre (1, 2, ou 3)')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Génération des bulletins pour le trimestre {trimestre} '
                f'de l\'année {annee_scolaire}'
            )
        )

        # Filtrer les classes si spécifié
        classes_query = Classe.objects.filter(annee_scolaire=annee_scolaire)
        if classe_nom:
            classes_query = classes_query.filter(nom=classe_nom)

        bulletins_crees = 0
        bulletins_ignores = 0
        erreurs = 0

        for classe in classes_query:
            self.stdout.write(f'\nTraitement de la classe: {classe.nom}')
            
            # Vérifier qu'il y a un professeur principal
            if not classe.prof_principal:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  Aucun professeur principal défini pour {classe.nom}'
                    )
                )
                continue

            for eleve in classe.eleves.all():
                try:
                    with transaction.atomic():
                        # Vérifier si le bulletin existe déjà
                        bulletin, created = Bulletin.objects.get_or_create(
                            eleve=eleve,
                            classe=classe,
                            annee_scolaire=annee_scolaire,
                            trimestre=trimestre,
                            defaults={
                                'cree_par': classe.prof_principal.user,
                                'statut': 'BROUILLON'
                            }
                        )

                        if not created and not force:
                            self.stdout.write(f'  ⏭️  Bulletin existant pour {eleve.nom_complet}')
                            bulletins_ignores += 1
                            continue

                        # Vérifier si toutes les évaluations sont complètes
                        if not self.verifier_evaluations_completes(eleve, classe, trimestre, annee_scolaire):
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  ⚠️  Évaluations incomplètes pour {eleve.nom_complet}'
                                )
                            )
                            continue

                        # Générer le bulletin
                        self.generer_bulletin(bulletin, eleve, classe, trimestre, annee_scolaire)
                        
                        if created:
                            self.stdout.write(f'  ✅ Bulletin créé pour {eleve.nom_complet}')
                            bulletins_crees += 1
                        else:
                            self.stdout.write(f'  🔄 Bulletin mis à jour pour {eleve.nom_complet}')
                            bulletins_crees += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ Erreur pour {eleve.nom_complet}: {str(e)}'
                        )
                    )
                    erreurs += 1

        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Génération terminée:\n'
                f'  • Bulletins créés/mis à jour: {bulletins_crees}\n'
                f'  • Bulletins ignorés: {bulletins_ignores}\n'
                f'  • Erreurs: {erreurs}'
            )
        )

    def verifier_evaluations_completes(self, eleve, classe, trimestre, annee_scolaire):
        """Vérifie si toutes les évaluations sont complètes pour l'élève"""
        # Récupérer toutes les matières enseignées dans la classe
        matieres = Matiere.objects.filter(
            professeurs__classes=classe
        ).distinct()

        for matiere in matieres:
            # Vérifier qu'il y a au moins une évaluation pour cette matière
            evaluations = Evaluation.objects.filter(
                matiere=matiere,
                trimestre=trimestre,
                annee_scolaire=annee_scolaire
            )

            if not evaluations.exists():
                return False

            # Vérifier que l'élève a une note pour chaque évaluation
            for evaluation in evaluations:
                if not Note.objects.filter(
                    eleve=eleve,
                    evaluation=evaluation,
                    note__isnull=False
                ).exists():
                    return False

        return True

    def generer_bulletin(self, bulletin, eleve, classe, trimestre, annee_scolaire):
        """Génère le contenu du bulletin"""
        # Calculer la moyenne générale
        moyenne_generale = self.calculer_moyenne_generale(eleve, trimestre, annee_scolaire)
        bulletin.moyenne_generale = moyenne_generale

        # Calculer le rang
        bulletin.rang = self.calculer_rang(eleve, classe, trimestre, annee_scolaire, moyenne_generale)

        # Informations sur la classe
        bulletin.effectif_classe = classe.eleves.count()
        bulletin.moyenne_classe = self.calculer_moyenne_classe(classe, trimestre, annee_scolaire)

        # Générer les notes détaillées par matière
        self.generer_notes_detaillees(bulletin, eleve, trimestre, annee_scolaire)

        # Recalculer automatiquement tous les champs
        bulletin.recalculer_tous_les_champs()

    def calculer_moyenne_generale(self, eleve, trimestre, annee_scolaire):
        """Calcule la moyenne générale de l'élève"""
        notes = Note.objects.filter(
            eleve=eleve,
            evaluation__trimestre=trimestre,
            evaluation__annee_scolaire=annee_scolaire,
            note__isnull=False
        ).select_related('evaluation__matiere')

        if not notes.exists():
            return None

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

    def calculer_rang(self, eleve, classe, trimestre, annee_scolaire, moyenne_generale):
        """Calcule le rang de l'élève dans sa classe"""
        if not moyenne_generale:
            return None

        # Compter le nombre d'élèves avec une moyenne supérieure
        bulletins_superieurs = Bulletin.objects.filter(
            classe=classe,
            annee_scolaire=annee_scolaire,
            trimestre=trimestre,
            moyenne_generale__gt=moyenne_generale,
            statut__in=['VALIDE', 'EN_ATTENTE']
        ).count()

        return bulletins_superieurs + 1

    def calculer_moyenne_classe(self, classe, trimestre, annee_scolaire):
        """Calcule la moyenne de la classe"""
        bulletins = Bulletin.objects.filter(
            classe=classe,
            annee_scolaire=annee_scolaire,
            trimestre=trimestre,
            moyenne_generale__isnull=False,
            statut__in=['VALIDE', 'EN_ATTENTE']
        )

        if bulletins.exists():
            moyenne = bulletins.aggregate(avg=Avg('moyenne_generale'))['avg']
            return round(moyenne, 2) if moyenne else None
        return None

    def generer_notes_detaillees(self, bulletin, eleve, trimestre, annee_scolaire):
        """Génère les notes détaillées par matière"""
        # Supprimer les anciennes notes détaillées
        bulletin.notes_detaillees.all().delete()

        # Récupérer toutes les matières avec leurs notes
        matieres = Matiere.objects.filter(
            professeurs__classes=bulletin.classe
        ).distinct()

        for matiere in matieres:
            # Calculer la moyenne de la matière
            notes_matiere = Note.objects.filter(
                eleve=eleve,
                evaluation__matiere=matiere,
                evaluation__trimestre=trimestre,
                evaluation__annee_scolaire=annee_scolaire,
                note__isnull=False
            )

            if notes_matiere.exists():
                # Calculer la moyenne pondérée
                total_points = 0
                total_coefficients = 0

                for note in notes_matiere:
                    coefficient = note.evaluation.matiere.coefficient
                    note_sur_20 = note.note_sur_20 or 0
                    total_points += note_sur_20 * coefficient
                    total_coefficients += coefficient

                if total_coefficients > 0:
                    moyenne_matiere = round(total_points / total_coefficients, 2)
                    
                    # Créer la note détaillée
                    NoteBulletin.objects.create(
                        bulletin=bulletin,
                        matiere=matiere,
                        moyenne_matiere=moyenne_matiere,
                        coefficient=matiere.coefficient,
                        appreciation=''  # À remplir par le professeur
                    )


