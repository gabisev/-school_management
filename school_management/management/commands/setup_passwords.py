from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from school_management.models import Eleve, Professeur

class Command(BaseCommand):
    help = 'Configure des mots de passe par défaut pour les élèves et professeurs'

    def handle(self, *args, **options):
        # Mot de passe par défaut pour les élèves (leur numéro étudiant)
        for eleve in Eleve.objects.all():
            user = eleve.user
            # Mot de passe = numéro étudiant
            user.set_password(eleve.numero_etudiant)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Mot de passe configuré pour l\'élève {eleve.user.get_full_name()} ({eleve.numero_etudiant})')
            )
        
        # Mot de passe par défaut pour les professeurs (leur nom d'utilisateur + "123")
        for professeur in Professeur.objects.all():
            user = professeur.user
            # Mot de passe = username + "123"
            user.set_password(user.username + "123")
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Mot de passe configuré pour le professeur {professeur.user.get_full_name()} ({user.username})')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Configuration terminée: {Eleve.objects.count()} élèves et {Professeur.objects.count()} professeurs')
        )