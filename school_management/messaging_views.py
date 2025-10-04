from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator

from .models import Conversation, Message, Participant, Classe, User
from .forms import ConversationForm, MessageForm, ParticipantForm
from .permissions import get_user_type


class ConversationListView(LoginRequiredMixin, ListView):
    """Vue pour lister les conversations de l'utilisateur"""
    model = Conversation
    template_name = 'school_management/messaging/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 10
    
    def get_queryset(self):
        """Filtrer les conversations selon le type d'utilisateur"""
        user = self.request.user
        user_type = get_user_type(user)
        
        # Récupérer les conversations où l'utilisateur est participant
        conversations = Conversation.objects.filter(
            participants__user=user,
            participants__actif=True,
            active=True
        ).annotate(
            last_message_time=Max('messages__date_envoi'),
            unread_count=Count('messages', filter=Q(
                messages__lu=False,
                messages__expediteur__isnull=False
            ) & ~Q(messages__expediteur=user))
        ).order_by('-last_message_time', '-date_modification')
        
        # Filtrer selon le type d'utilisateur
        if user_type == 'professeur':
            # Professeurs : peuvent voir toutes leurs conversations
            return conversations
        elif user_type == 'eleve':
            # Élèves : peuvent voir les conversations de leur classe et entre élèves
            return conversations.filter(
                Q(type_conversation='ELEVE_ELEVE') |
                Q(type_conversation='CLASSE_PROF', classe=user.eleve.classe)
            )
        elif user_type == 'parent':
            # Parents : peuvent voir les conversations avec les professeurs de leurs enfants
            # Récupérer l'instance Parent associée à l'utilisateur via la relation OneToOne
            try:
                parent_instance = user.parent
                enfants_classes = Classe.objects.filter(eleves__parents=parent_instance)
                return conversations.filter(
                    Q(type_conversation='PROF_PARENT') |
                    Q(type_conversation='CLASSE_PROF', classe__in=enfants_classes)
                )
            except:
                # Si pas d'instance Parent, retourner les conversations PROF_PARENT seulement
                return conversations.filter(type_conversation='PROF_PARENT')
        else:
            # Admin : peut voir toutes les conversations
            return conversations
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = get_user_type(self.request.user)
        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher une conversation et ses messages"""
    model = Conversation
    template_name = 'school_management/messaging/conversation_detail.html'
    context_object_name = 'conversation'
    
    def get_queryset(self):
        """Filtrer les conversations accessibles à l'utilisateur"""
        user = self.request.user
        return Conversation.objects.filter(
            participants__user=user,
            participants__actif=True,
            active=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()
        user = self.request.user
        
        # Récupérer les messages de la conversation
        messages_list = conversation.messages.all().order_by('date_envoi')
        
        # Marquer les messages comme lus
        for message in messages_list:
            if message.expediteur != user and not message.lu:
                message.marquer_comme_lu()
        
        # Pagination des messages
        paginator = Paginator(messages_list, 20)
        page_number = self.request.GET.get('page')
        messages_page = paginator.get_page(page_number)
        
        context['messages'] = messages_page
        context['message_form'] = MessageForm()
        context['participants'] = conversation.get_participants()
        context['user_type'] = get_user_type(user)
        
        # Vérifier les permissions du créateur
        context['can_manage_participants'] = conversation.peut_gerer_participants(user)
        context['is_creator'] = conversation.est_createur(user)
        
        return context


class ConversationCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle conversation"""
    model = Conversation
    form_class = ConversationForm
    template_name = 'school_management/messaging/conversation_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Restreindre l'accès aux professeurs et administrateurs uniquement"""
        user = request.user
        user_type = get_user_type(user)
        
        # Seuls les professeurs et administrateurs peuvent créer des conversations
        if user_type not in ['professeur', 'admin']:
            messages.error(request, "Seuls les professeurs et administrateurs peuvent créer des conversations.")
            return redirect('school_management:conversation_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        conversation = form.save(commit=False)
        conversation.createur = self.request.user  # Définir le créateur
        conversation.save()
        
        # Ajouter le créateur comme participant
        Participant.objects.create(
            conversation=conversation,
            user=self.request.user
        )
        
        messages.success(
            self.request,
            f'Conversation "{conversation.titre}" créée avec succès.'
        )
        
        return redirect('school_management:conversation_detail', pk=conversation.pk)


class ConversationUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une conversation"""
    model = Conversation
    form_class = ConversationForm
    template_name = 'school_management/messaging/conversation_form.html'
    
    def get_queryset(self):
        """Seuls les participants peuvent modifier"""
        user = self.request.user
        return Conversation.objects.filter(
            participants__user=user,
            participants__actif=True
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


@login_required
def send_message(request, conversation_id):
    """Vue pour envoyer un message dans une conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants__user=request.user,
        participants__actif=True,
        active=True
    )
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.expediteur = request.user
            message.save()
            
            # Mettre à jour la date de modification de la conversation
            conversation.date_modification = timezone.now()
            conversation.save()
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Message envoyé avec succès.',
                    'message_id': message.id
                })
            else:
                messages.success(request, 'Message envoyé avec succès.')
                return redirect('school_management:conversation_detail', pk=conversation.pk)
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    
    return redirect('school_management:conversation_detail', pk=conversation.pk)


@login_required
def add_participants(request, conversation_id):
    """Vue pour ajouter des participants à une conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants__user=request.user,
        participants__actif=True
    )
    
    # Vérifier que l'utilisateur est le créateur de la conversation
    if not conversation.peut_gerer_participants(request.user):
        messages.error(request, "Seul le créateur de la conversation peut ajouter des participants.")
        return redirect('school_management:conversation_detail', pk=conversation.pk)
    
    if request.method == 'POST':
        form = ParticipantForm(request.POST, conversation=conversation)
        if form.is_valid():
            users = form.cleaned_data['user']
            for user in users:
                Participant.objects.get_or_create(
                    conversation=conversation,
                    user=user
                )
            
            messages.success(
                request,
                f'{len(users)} participant(s) ajouté(s) avec succès.'
            )
            return redirect('school_management:conversation_detail', pk=conversation.pk)
    else:
        form = ParticipantForm(conversation=conversation)
    
    return render(request, 'school_management/messaging/add_participants.html', {
        'form': form,
        'conversation': conversation
    })


@login_required
def remove_participant(request, conversation_id, user_id):
    """Vue pour retirer un participant d'une conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants__user=request.user,
        participants__actif=True
    )
    
    # Vérifier que l'utilisateur est le créateur de la conversation
    if not conversation.peut_gerer_participants(request.user):
        messages.error(request, "Seul le créateur de la conversation peut retirer des participants.")
        return redirect('school_management:conversation_detail', pk=conversation.pk)
    
    participant = get_object_or_404(
        Participant,
        conversation=conversation,
        user_id=user_id
    )
    
    # Ne pas permettre de retirer le créateur
    if participant.user == conversation.createur:
        messages.error(request, "Le créateur de la conversation ne peut pas être retiré.")
    else:
        participant.actif = False
        participant.save()
        
        messages.success(
            request,
            f'{participant.user.get_full_name()} retiré de la conversation.'
        )
    
    return redirect('school_management:conversation_detail', pk=conversation.pk)


@login_required
def get_conversation_messages(request, conversation_id):
    """Vue AJAX pour récupérer les messages d'une conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants__user=request.user,
        participants__actif=True
    )
    
    # Récupérer les messages depuis une date donnée
    since = request.GET.get('since')
    if since:
        try:
            since_date = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
            messages_list = conversation.messages.filter(
                date_envoi__gt=since_date
            ).order_by('date_envoi')
        except ValueError:
            messages_list = conversation.messages.all().order_by('-date_envoi')[:10]
    else:
        messages_list = conversation.messages.all().order_by('-date_envoi')[:10]
    
    # Marquer les messages comme lus
    for message in messages_list:
        if message.expediteur != request.user and not message.lu:
            message.marquer_comme_lu()
    
    messages_data = []
    for message in messages_list:
        messages_data.append({
            'id': message.id,
            'contenu': message.contenu,
            'expediteur': message.expediteur.get_full_name(),
            'date_envoi': message.date_envoi.isoformat(),
            'lu': message.lu
        })
    
    return JsonResponse({
        'messages': messages_data,
        'conversation_id': conversation.id
    })


@login_required
def messaging_dashboard(request):
    """Vue pour le tableau de bord de la messagerie"""
    user = request.user
    user_type = get_user_type(user)
    
    # Statistiques
    conversations_count = Conversation.objects.filter(
        participants__user=user,
        participants__actif=True,
        active=True
    ).count()
    
    unread_messages_count = Message.objects.filter(
        conversation__participants__user=user,
        conversation__participants__actif=True,
        lu=False
    ).exclude(expediteur=user).count()
    
    # Conversations récentes
    recent_conversations = Conversation.objects.filter(
        participants__user=user,
        participants__actif=True,
        active=True
    ).annotate(
        last_message_time=Max('messages__date_envoi')
    ).order_by('-last_message_time')[:5]
    
    context = {
        'conversations_count': conversations_count,
        'unread_messages_count': unread_messages_count,
        'recent_conversations': recent_conversations,
        'user_type': user_type
    }
    
    return render(request, 'school_management/messaging/dashboard.html', context)
