# Classe CRON per far scadere le aste

from django_cron import CronJobBase, Schedule
from datetime import timedelta
from django.utils import timezone
from .models import *

class AuctionExpiring(CronJobBase):
    RUN_EVERY_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'webauction.auction_expire'    # a unique code

    def do(self):
        # ---------- Controllo l'incremento degli auction token --------------
        nonPremiumUser = UserProfile.objects.filter(premium__exact=False)
        now = timezone.localtime(timezone.now())
        for user in nonPremiumUser:
            # Il primo di ogni mese alle ore 0 e 0 minuti incremento
            # il token, incentivando quindi fortemente al premium
            if now.day == 1 and now.hour == 0 and now.minute == 1:
                if user.auction_count < MAX_AUCT_COUNT:
                    user.auction_count = user.auction_count + 1
                    user.save()

        # -------------- Controllo tutti gli oggetti premium ---------------
        premiumAuction = Auction.objects.filter(active__exact=True, premium_active__exact=True)
        for auction in premiumAuction:
            elapsed = now - auction.premium_date
            time_difference = elapsed.total_seconds()
            print(time_difference)
            if time_difference >= 0:
                auction.premium_active=False
                auction.save()

        # -------------- Controllo Aste in corso -----------------------------
        all_active_auctions = Auction.objects.filter(active=True)
        for auction in all_active_auctions:
            elapsed = now - auction.expire_date
            time_difference = elapsed.total_seconds()
            print(time_difference)
            if time_difference >= 0:
                print(auction.title + ' ...Getting disabled')
                auction.active = False
                auction.save()
                allFollowed = FollowedAuction.objects.filter(auction=auction)
                for follow in allFollowed:
                    follow.isActive = False
                    follow.save()
                seller = auction.seller
                sellerProfile = get_object_or_404(UserProfile, user=seller)
                if auction.last_bid_user != None:
                    sellerProfile.sold_auction = sellerProfile.sold_auction + 1
                    sellerProfile.save()
