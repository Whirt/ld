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
        now = timezone.localtime(timezone.now())
        all_active_auctions = Auction.objects.filter(active=True)
        for auction in all_active_auctions:
            elapsed = now - auction.expire_date
            time_difference = elapsed.total_seconds()
            print(time_difference)
            if time_difference >= 0:
                print(auction.title + ' ...Getting disabled')
                auction.active = False
                auction.save()
                seller = auction.seller
                sellerProfile = get_object_or_404(UserProfile, user=seller)
                if auction.last_bid_user != None:
                    sellerProfile.sold_auction = sellerProfile.sold_auction + 1
                    sellerProfile.save()
