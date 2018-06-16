# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views import generic
from webauction.models import UserProfile
from .models import *
from .forms import *
from django.utils import timezone

@login_required
def messenger(request):
    left_notification = ''
    right_notification = ''
    user_chat_with = 'None'
    chat_selected = False
    all_messages_sorted = ['No messages']
    sorted_messages = ['No messages']
    if request.method == 'POST':
        if 'accept' in request.POST:
            accepted_username = request.POST['accept_user']
            accepted_user = User.objects.get(username=accepted_username)
            print(request.user.username + " " + accepted_user.username)
            friendRequest = FriendRequest.objects.get(
                Q(friend_of__exact=accepted_user), Q(friend__exact=request.user))
            friendRequest.accepted = True
            friendRequest.save()
            left_notification += 'Friend accepted'
        if 'chat' in request.POST:
            # Qui ordino secondo la data
            #sorted_messages = sorted(all_messages, key=lambda x: x.datetime)
            user_chat_with = User.objects.get(username=request.POST['user_chat'])
            chat_selected = True
        if 'new_message' in request.POST:
            chat_selected = True
            messageToBeSent = request.POST['messageToBeSent']
            username_chat_with = request.POST['username_chat_with']
            user_chat_with = User.objects.get(username=username_chat_with)
            print('Chatto con ' + user_chat_with.username)
            if len(messageToBeSent) == 0:
                right_notification += 'Message cannot be null'
            elif len(messageToBeSent) > MAX_MESSAGE_LENGTH():
                right_notification += 'Message too long'
            else:
                new_message = Message(sender=request.user, receiver=user_chat_with,
                                message=messageToBeSent)
                new_message.save()

    if chat_selected:
        all_sent_messages = list(Message.objects.filter(
                Q(sender=request.user), Q(receiver=user_chat_with)))
        all_received_messages = list(Message.objects.filter(
                Q(sender=user_chat_with), Q(receiver=request.user)))
        all_messages = all_sent_messages + all_received_messages
        # L'ordinamento avviene tramite la data, si ottiene la data,
        # ne si calcola la differenza rispetto il momento attuale e
        # in base alla differenza in secondi si mostra in ordine crescente
        # di tempo, per ottenere dai più recenti ai più vecchi
        now = timezone.localtime(timezone.now())
        all_messages_sorted = sorted(all_messages,
            key=lambda x: (now-x.datetime).total_seconds() , reverse=False)

    # Richieste inviate all'utente in attesa di conferma
    friendRequests = FriendRequest.objects.filter(Q(friend__exact=request.user), Q(accepted__exact=False))

    # Tutti gli amici
    all_friends_first_part = [ friendrequest.friend for friendrequest in
            FriendRequest.objects.filter(Q(friend_of__exact=request.user), Q(accepted__exact=True))]
    all_friends_second_part = [ friendrequest.friend_of for friendrequest in
            FriendRequest.objects.filter(Q(friend__exact=request.user), Q(accepted__exact=True))]

    # per costruzione all_friend non ha rindondanze!
    all_friends = all_friends_first_part + all_friends_second_part
    all_friendsProfiles = [ UserProfile.objects.get(user=friend) for friend in all_friends]
    friends_plus_profile = [ (all_friends[i], all_friendsProfiles[i])
                             for i in range(0, len(all_friends))]


    # Nel caso due utenti accettino la stessa richiesta reciproca nello stesso
    # momento, anche se non c'è atomicità il risultato è sempre lo stesso!
    return render(request, 'messenger/messenger_page.html',
            {'friendRequests':friendRequests,
             'friends_plus_profile':friends_plus_profile,
             'left_notification':left_notification,
             'right_notification':right_notification,
             'numFriends': len(all_friends),
             'chat_selected':chat_selected,
             'user_chat_with':user_chat_with,
             'messages':all_messages_sorted})


class SearchUserView(generic.ListView):
    template_name = 'messenger/search_user.html'
    context_object_name = 'matching_user_list'

    def get_queryset(self):
        keywords = self.request.GET.get('keywords')
        print('keyword da provare: ' + keywords)
        keywords = keywords.split()
        # Ricerca in OR degli utenti
        result_set = set()
        for keyword in keywords:
            users = User.objects.filter(Q(username__icontains=keyword),
                                                    is_active__exact=True)
            for user in users: # mi serve il profilo per fare il render del profile pic
                userProfile = UserProfile.objects.get(user=user)
                result_set.add(userProfile)

        return list(result_set)
