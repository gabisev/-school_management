from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from school_management.models import Eleve, Professeur

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates User objects for existing Eleve instances and sets up authentication.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up User objects for existing students and teachers...'))

        # Handle Eleve users
        eleves = Eleve.objects.filter(user__isnull=True)
        for eleve in eleves:
            # Create username from student number
            username = eleve.numero_etudiant
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User with username {username} already exists. Skipping.'))
                continue
            
            # Create User object
            user = User.objects.create_user(
                username=username,
                first_name=eleve.prenom,
                last_name=eleve.nom,
                email=eleve.email if eleve.email else f'{username}@school.local',
                password=username  # Default password is student number
            )
            
            # Link to Eleve
            eleve.user = user
            eleve.save()
            
            self.stdout.write(self.style.SUCCESS(f'Created User for Eleve {eleve.nom} {eleve.prenom} (Username: {username}, Password: {username})'))

        # Handle Professeur users that might be missing
        professeurs = Professeur.objects.filter(user__isnull=True)
        for professeur in professeurs:
            # Create username from user's name
            if professeur.user:
                username = professeur.user.username
            else:
                # This shouldn't happen since Professeur requires a user, but just in case
                username = f"prof{professeur.id}"
            
            self.stdout.write(self.style.WARNING(f'Professeur {professeur} already has user: {professeur.user}'))

        self.stdout.write(self.style.SUCCESS('User setup complete!'))
        
        # Display summary
        total_eleves = Eleve.objects.count()
        eleves_with_users = Eleve.objects.filter(user__isnull=False).count()
        total_professeurs = Professeur.objects.count()
        professeurs_with_users = Professeur.objects.filter(user__isnull=False).count()
        
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  - Eleves: {eleves_with_users}/{total_eleves} have User accounts')
        self.stdout.write(f'  - Professeurs: {professeurs_with_users}/{total_professeurs} have User accounts')
