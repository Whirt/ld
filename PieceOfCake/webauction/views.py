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
from chartit import DataPool, Chart

def index(request):
    return render(request, 'webauction/index.html')

class SearchView(generic.ListView):
    template_name = 'webauction/search.html'
    context_object_name = 'context'

    def get_queryset(self):
        context = {}
        keywords = self.request.GET.get('keywords')
        keywords = keywords.lower()
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

        # Caso in cui la ricerca in AND (di default)
        if category != None and category != 'ALL':
            selected_auctions = Auction.objects.filter(active__exact=True, category__exact=category)
        else:
            selected_auctions = Auction.objects.filter(active__exact=True)
        keywords = keywords.split()
        for keyword in keywords:
            # Selected_acution passo a passo subisce l'AND con ogni keyword
            selected_auctions = [ auction for auction in selected_auctions
                                if keyword in auction.title.lower() ]

        # Sorting
        order_dir = self.request.GET.get('order_dir')
        direction = False # going Up
        if order_dir == 'HighToLow':
            direction = True
        order_by = self.request.GET.get('order_by')
        if order_by == 'Data':
            now = timezone.localtime(timezone.now())
            selected_auctions = sorted(selected_auctions, \
                key=lambda x: (now-x.pub_date).total_seconds() , reverse=direction)
        if order_by == 'Price':
            selected_auctions = sorted(selected_auctions, \
                key=lambda x: x.current_price , reverse=direction)
        if order_by == 'Reliability':
            selected_auctions = sorted(selected_auctions, \
                key=lambda x:
                # Di queste ordino sui feedback dei venditori
                # !!!!!!!!!!!!!! DA TESTARE
                get_object_or_404(UserProfile, user=x.seller).feedback , reverse=direction)

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
# in quanto non si riuscirebbe a tirar fuori la request.user in maniera semplice
# e altri parametri utili
def detail_auction(request, product_key):
    context = {}
    auction = get_object_or_404(Auction, pk=product_key)
    context['auction'] = auction
    context['sellerProfile'] = get_object_or_404(UserProfile, user=auction.seller)

    if auction.active:
        # Differenza dei tempi per lo script
        now = timezone.localtime(timezone.now())
        elapsed = auction.expire_date - now
        time_difference = elapsed.total_seconds()
        context['time_diff_seconds'] = time_difference

    if request.method == 'POST' and not auction.premium_active:
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
        else: # Caso di successo

            # Controllo il followed di quello che ha scommesso precedentemente
            if auction.last_bid_user != None:
                getLastBidder = User.objects.filter(id__exact=auction.last_bid_user.id)
                # Aggiorno il suo FollowedAuction
                getHisFollowedAuction = FollowedAuction.objects.get(
                            auction__exact=auction, follower=getLastBidder)
                getHistFollowedAuction.outBiddedBy = request.user
            # Controllo se esisteva gia un precedente followed
            updateFollowed = FollowedAuction.objects.filter(
                    auction__exact=auction, follower__exact=request.user)
            if len(updateFollowed) == 0:
                newFollowed = FollowedAuction(auction=auction, follower=request.user,
                            outBiddedBy=None)
                newFollowed.save()
            else:
                updateFollowed.outBiddedBy = None

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
    userProfile = UserProfile.objects.get(user=request.user)
    context['userProfile'] = userProfile
    if request.method == 'POST':
        form = MakeAuctionForm(request.POST, request.FILES)

        if not userProfile.premium and userProfile.auction_count == 0:
            form = MakeAuctionForm()
            context['form'] = form
            context['error_message'] = 'Insufficient auction token'
            return render(request, 'webauction/make_auction.html', context)

        error_message = ''

        norm_days = request.POST['norm_days']
        norm_hours = request.POST['norm_hours']
        norm_minutes = request.POST['norm_minutes']
        prem_days = request.POST['prem_days']
        prem_hours = request.POST['prem_hours']
        prem_minutes = request.POST['prem_minutes']
        print(norm_days + ' ' + norm_hours + ' ' + norm_minutes)
        print(prem_days + ' ' + prem_hours + ' ' + prem_minutes)
        norm_days = int(norm_days)
        norm_hours = int(norm_hours)
        norm_minutes = int(norm_minutes)
        prem_days = int(prem_days)
        prem_hours = int(prem_hours)
        prem_minutes = int(prem_minutes)
        if norm_days == 0 and norm_hours == 0 and norm_minutes == 0:
            error_message += ' Duration cannot be zero.'
        # controllo anche a lato server oltre che a livello di input form
        elif norm_days < 0 or norm_hours < 0 or norm_minutes < 0 or \
             prem_days < 0 or prem_hours < 0 or prem_minutes < 0 or \
             prem_minutes >= 60 or prem_hours >= 24 or prem_days >= MAX_DURATION_DAY() or \
             norm_minutes >= 60 or norm_hours >= 24 or norm_days >= MAX_DURATION_DAY():
            error_message += ' Invalid duration value.'

        now = timezone.localtime(timezone.now())
        premium_date = now + timedelta(days=prem_days, hours=prem_hours, minutes=prem_minutes)
        expire_date = now + timedelta(days=norm_days+prem_days,
            hours=norm_hours+prem_hours, minutes=norm_minutes+prem_minutes)
        premium_state = True
        if not userProfile.premium or (prem_days == 0 and prem_hours == 0 and prem_minutes == 0):
            premium_state = False

        if error_message == '' and form.is_valid():
            seller = request.user
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
                            premium_date = premium_date, premium_active = premium_state,
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

def get_pool(auctions):

    len_sold_auction = len(auctions)
    if len_sold_auction == 0:
        return

    ds = DataPool(
        series = [
            {
            'options': {'source': auctions},
            'terms':   ['expire_date','current_price']
            }
        ]
    )
    chrt = Chart(
        datasource = ds,
        series_options = [
            {
            'options':{'type':'line', 'stacking':False},
            'terms':{'expire_date': ['current_price']}
            }
        ],
        chart_options = {
            'title': {'text':''},
            'xAxis': {
                'title': {'text':'Data'}
            }
        }
    )

    return chrt

def expired_won_auction(searched_user):

    return get_pool(won_auction)


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
                    Q(friend_of__exact=request.user))
    friendRequests_backward = FriendRequest.objects.filter(
                    Q(friend__exact=request.user))
    friends_forward = [ friendrequest.friend for friendrequest in friendRequests_forward ]
    friends_backward = [ friendrequest.friend_of for friendrequest in friendRequests_backward ]
    requestIsSent = False
    requestIsSentBack = False
    if searchedUser in friends_forward:
        requestIsSent = True
    if searchedUser in friends_backward:
        requestIsSentBack = True

    # Controllo se esiste gia un voto da parte dell'utente visitatore
    voteAlreadyExists = False
    existingVote = Vote.objects.filter(receiver=userProfile.user, sender=request.user)
    if len(existingVote) != 0:
        voteAlreadyExists = True

    # Calcolo i grafici
    sold_auction = Auction.objects.filter(Q(seller__exact=userProfile.user, active__exact=False),
        ~Q(last_bid_user__exact=None))
    now = timezone.localtime(timezone.now())
    sorted_sold_auction = sorted(sold_auction, \
        key=lambda x: (now-x.pub_date).total_seconds() , reverse=False)
    chart_expired = get_pool(sold_auction)
    chart_won = []

    sorted_won_auction = []
    if userProfile.user == request.user:
        won_auction = Auction.objects.filter(last_bid_user__exact=request.user, active__exact=False)
        now = timezone.localtime(timezone.now())
        sorted_won_auction = sorted(won_auction, \
            key=lambda x: (now-x.pub_date).total_seconds() , reverse=False)
        chart_won = get_pool(won_auction)

    # Colleziono il context
    context = {}
    context['userProfile'] = userProfile
    context['alreadySentForward'] = requestIsSent
    context['alreadySentBack'] = requestIsSentBack
    context['activeAuctions'] = active_auction_list
    context['sorted_sold_auction'] = sorted_sold_auction
    context['sorted_won_auction'] = sorted_won_auction
    context['charts'] = [chart_expired, chart_won]

    all_votes = Vote.objects.filter(receiver__exact=userProfile.user)
    # L'ordinamento avviene tramite la data, si ottiene la data,
    # ne si calcola la differenza rispetto il momento attuale e
    # in base alla differenza in secondi si mostra in ordine crescente
    # di tempo, per ottenere dai più recenti ai più vecchi
    now = timezone.localtime(timezone.now())
    all_votes_sorted = sorted(all_votes,
        key=lambda x: (now-x.datetime).total_seconds(), reverse=False)
    context['all_votes'] = all_votes_sorted

    # Get all active following auction
    # Nota: Se anche dopo aver vinto compare tra le active probabilmente non è stato
    # attivato la cron function!
    followedAuctions = FollowedAuction.objects.filter(
        Q(follower__exact=request.user), Q(isActive__exact=True))
    context['followedAuctions'] = followedAuctions

    if request.method == 'GET':
        return render(request, 'webauction/profile.html', context)

    if request.method == 'POST':
        success_message = ''

        # --- Switch Case dei possibili eventi che hanno generato il POST ------

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
        elif not voteAlreadyExists and 'new_vote' in request.POST:
            # Suppongo che nessun utente possa votare due volte
            # lo stesso utente, quindi devo effettuare un controllo.
            # Ma il controllo viene fatto gia a livello di template, che non visualizza
            # la possibilità di votare nel caso in cui esista gia
            vote = request.POST['rating']
            vote = int(vote)
            rating_message = request.POST['rateMessage']
            new_vote = Vote(sender=request.user, receiver=userProfile.user,
                            message=rating_message, datetime=datetime,
                            rating=vote)
            new_vote.save()
            voteAlreadyExists = True
            success_message = 'Rated successfully'
            # lo aggiungo ai voti così si vede direttamente
            all_votes_sorted.append(new_vote)

        context['voteExists'] = voteAlreadyExists

        context['notification'] = success_message
        return render(request, 'webauction/profile.html', context)
