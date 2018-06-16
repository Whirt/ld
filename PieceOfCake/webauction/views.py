# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render,  get_object_or_404, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views import generic
from messenger.models import FriendRequest
from .models import *
from .forms import *
import math
from datetime import timedelta
from django.utils import timezone

def index(request):
    return render(request, 'webauction/index.html')

class SearchView(generic.ListView):
    template_name = 'webauction/search.html'
    context_object_name = 'context'

    def get_queryset(self):
        context = {}
        keywords = self.request.GET.get('keywords')
        category = self.request.GET.get('category_choice')
        if category != None:
            print('category:' + str(category))
        print('keywords da provare: ' + keywords)

        """
        Questo e' il caso in cui di default la ricerca sia in OR
        # L'ordinamento consiste in due dictionary
        # 1) uno per mantenere in memoria il titolo delle auction
        # 2) uno per il punteggio relativo in un dictionary
        result_set = set() # sfrutto l'unicità dei set
        auction_score = {}
        for keyword in keywords:
            selected_auctions = Auction.objects.filter(Q(title__icontains=keyword),
                                                    active__exact=True)
            for auctions in selected_auctions:
                if auctions not in result_set:
                    # prima volta che si trova in set
                    auction_score[auctions] = 1
                else:
                    # un oggetto che contiene piu' keywords viene privilegiato
                    auction_score[auctions] = auction_score[auctions]+1
                result_set.add(auctions)

        sorted_result = sorted(auction_score.items(), key=lambda x: x[1], reverse=True)
        sorted_result = [ x[0] for x in sorted_result ]
        """

        # Caso in cui la ricerca sia di default in AND
        if category != None and category != 'ALL':
            selected_auctions = Auction.objects.filter(active__exact=True, category__exact=category)
        else:
            selected_auctions = Auction.objects.filter(active__exact=True)

        print(len(selected_auctions))

        keywords = keywords.split()
        for keyword in keywords:
            selected_auctions = [ auction for auction in selected_auctions
                                if keyword in auction.title ]

        # Di queste ordino sui feedback dei venditori
        # !!!!!!!!!!!!!! DA IMPLEMENTARE

        # Ordino in maniera visualizzabile su template li raggruppo
        VISUAL_GROUP = 2
        num_group = int(math.ceil(len(selected_auctions)/float(VISUAL_GROUP)))
        grouped_selected_auctions = []
        for i in range(0, num_group):
            grouped_selected_auctions.append(
                selected_auctions[i*VISUAL_GROUP : (i+1)*VISUAL_GROUP])
        context['matching_auction_list'] = grouped_selected_auctions

        if keywords == 'advanced_search':
            context['advanced'] = True

        return context


# In questo caso conviene usare la view diretto piuttosto che detail view
# in quanto non si riuscirebbe a tirar fuori la request.user e altri parametri utili
def detail_auction(request, product_key):
    context = {}
    auction = get_object_or_404(Auction, pk=product_key)
    context['auction'] = auction
    context['sellerProfile'] = get_object_or_404(UserProfile, user=auction.seller)

    if request.method == 'POST':
        new_bid = request.POST['bid_value']
        new_bid = new_bid.replace(',','.')
        new_bid = float(new_bid)
        current_price = float(auction.current_price)
        min_bid = float(auction.min_bid)
        error_message = ''
        if new_bid <= current_price:
            error_message = 'Incorrect value'
        elif auction.last_bid_user == request.user:
            error_message = 'You are the current best bidder'
        elif auction.seller == request.user:
            error_message = 'Bidding on own auction is forbidden'
        else:
            context['success_message'] = 'New bid successfully made'
            auction.last_bid_user = request.user
            auction.current_price = new_bid
            auction.bid_count = auction.bid_count + 1
            auction.save()
        context['error_message'] = error_message
    return render(request, 'webauction/auction_detail.html', context)

@login_required
def success_created(request, product_key):
    return render(request, 'webauction/success_created.html', {'auction_pk': product_key})

@login_required
def make_auction(request):
    context = {}
    if request.method == 'POST':
        form = MakeAuctionForm(request.POST, request.FILES)
        try:
            user = User.objects.get(id=request.user.id)
            userProfile = UserProfile.objects.get(user=user)
        except User.DoesNotExist:
            form = MakeAuctionForm()
            context['form'] = form
            context['error_message'] = 'System error: user not exists'
            return render(request, 'webauction/make_auction.html', context)
        if not userProfile.premium and userProfile.auction_count == 0:
            form = MakeAuctionForm()
            context['form'] = form
            context['error_message'] = 'Insufficient auction token'
            return render(request, 'webauction/make_auction.html', context)

        error_message = ''

        days = request.POST['days']
        hours = request.POST['hours']
        minutes = request.POST['minutes']
        print(days + ' ' + hours + ' ' + minutes)
        days = int(days)
        hours = int(hours)
        minutes = int(minutes)
        now = timezone.localtime(timezone.now())
        expire_date = now + timedelta(days=days, hours=hours, minutes=minutes)
        if days == 0 and hours == 0 and minutes == 0:
            error_message += ' Duration cannot be zero.'
        # controllo anche a lato server oltre che a livello di input form
        elif days < 0 or hours < 0 or minutes < 0 or \
             minutes >= 60 or hours >= 24 or days >= MAX_DURATION_DAY():
            error_message += ' Invalid duration value.'

        if error_message == '' and form.is_valid():
            seller = user
            title = form.cleaned_data['title']
            image = form.cleaned_data['image']
            description = form.cleaned_data['description']
            min_price = form.cleaned_data['min_price']
            current_price = min_price
            min_bid = form.cleaned_data['min_bid']
            category = form.cleaned_data['category']
            #expire_date

            if min_bid < MIN_BID() or min_price < min_bid:
                error_message += ' Invalid price or minimum value.'
            else:
                auction = Auction(seller=seller, title=title, description=description,
                            image=image, expire_date=expire_date, min_price=min_price,
                            current_price = min_price, category=category, min_bid=min_bid)
                auction.save()
                if not userProfile.premium:
                    userProfile.auction_count = userProfile.auction_count - 1
                userProfile.save()
                return HttpResponseRedirect(reverse('webauction:success', args=[auction.id]))
        else:
            error_message += ' Check again the form.'

        # Error case
        form = MakeAuctionForm()
        context['form'] = form
        context['error_message'] = error_message
        return render(request, 'webauction/make_auction.html', context)
    if request.method == 'GET':
        # caso di un GET
        form = MakeAuctionForm()
        context['form'] = form
        return render(request, 'webauction/make_auction.html', context)



def profile(request, searched_username):
    if searched_username == '':
        searchedUser = request.user
    else:
        searchedUser = get_object_or_404(User, username=searched_username)
    userProfile = get_object_or_404(UserProfile, user=searchedUser)

    # mostro le auction attive
    active_auction_list = Auction.objects.filter(Q(seller__exact=searchedUser),Q(active__exact=True))

    # Controllo tutte quelle nella direzione da utente ad altri
    friendRequests_forward = FriendRequest.objects.filter(
                    Q(friend_of__exact=request.user), Q(accepted__exact=False))
    friendRequests_backward = FriendRequest.objects.filter(
                    Q(friend__exact=request.user), Q(accepted__exact=False))
    friends_forward = [ friendrequest.friend for friendrequest in friendRequests_forward ]
    friends_backward = [ friendrequest.friend_of for friendrequest in friendRequests_backward ]
    requestIsSent = False
    requestIsSentBack = False
    if searchedUser in friends_forward:
        requestIsSent = True
    if searchedUser in friends_backward:
        requestIsSentBack = True

    context = {}
    context['userProfile'] = userProfile
    context['alreadySentForward'] = requestIsSent
    context['alreadySentBack'] = requestIsSentBack
    context['activeAuctions'] = active_auction_list
    if request.method == 'GET':
        return render(request, 'webauction/profile.html', context)

    if request.method == 'POST':
        success_message = ''

        # se si tratta di una richiesta di amicizia
        if 'friend_request' in request.POST:
            friendRequests = FriendRequest.objects.filter(
                            Q(friend_of__exact=request.user), Q(friend__exact=searchedUser))
            if len(friendRequests) != 0:
                context['notification'] = 'Request already sent'
                return render(request, 'webauction/profile.html', context)
            new_request = FriendRequest(friend_of=request.user, friend=searchedUser)
            new_request.save()
            requestIsSent = True
            success_message = 'Friend request sent'

        # se si tratta di un aggiornamento della descrizione
        elif 'update_desc' in request.POST:
            new_description = request.POST['description']
            # C'è un controllo client side fatto con javascript e questo
            # è il controllo serverside!
            if len(new_description) > MAX_DESCRIPTION_LEN():
                context['error_message'] = 'Description maximum length overreached'
                return render(request, 'webauction/profile.html', context)
            userProfile.description = new_description
            userProfile.save()
            success_message = 'Description updated successfully'

        # se si tratta di un aggiornamento dell'immagine profilo
        elif 'update_img' in request.POST:
            new_profile_pic = request.FILES['update_pic']
            # potrebbe starci per motivi di sicurezza un controllo dimensione file
            # ma vado offtopic
            userProfile.profile_pic = new_profile_pic
            userProfile.save()
            success_message = 'Image update successfully'

        #se si tratta del diventare premium
        elif 'get_premium' in request.POST:
            userProfile.premium = True
            userProfile.save()
            success_message = 'Premium activated'

        context['notification'] = success_message
        return render(request, 'webauction/profile.html', context)
