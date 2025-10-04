from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from school_management.models import Parent


class Command(BaseCommand):
    help = 'Met à jour les mots de passe des parents avec le numéro de leur premier enfant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        parents = Parent.objects.filter(user__isnull=False)
        updated_count = 0
        
        self.stdout.write(f"Traitement de {parents.count()} parents...")
        
        for parent in parents:
            enfants = parent.eleves.filter(statut=True).order_by('nom', 'prenom')
            
            if enfants.exists():
                premier_enfant = enfants.first()
                nouveau_mot_de_passe = premier_enfant.numero_etudiant
                
                if not dry_run:
                    parent.user.set_password(nouveau_mot_de_passe)
                    parent.user.save()
                
                self.stdout.write(
                    f"{'[DRY-RUN] ' if dry_run else ''}Parent {parent.get_nom_complet()} "
                    f"-> Mot de passe: {nouveau_mot_de_passe} (enfant: {premier_enfant.nom_complet})"
                )
                updated_count += 1
            else:
                self.stdout.write(
                    f"Parent {parent.get_nom_complet()} n'a pas d'enfants liés"
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Mode dry-run: {updated_count} parents seraient mis à jour")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"{updated_count} parents ont été mis à jour avec succès")
            )






