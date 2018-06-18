# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import UserProfile, Auction, Vote, FollowedAuction


# Ordino gli elementi in modo tale che i campi
# più sensati se lasciati di default in fondo
# gli altri sono gia ragionevoli

class AuctionAdmin(admin.ModelAdmin):
    fields = ['seller','title','image', \
        'expire_date','premium_date','category',
        'current_price', 'min_price',
        'description',

        # Infine gli elementi tipicamente lasciati al default
        'premium_active', 'bid_count', 'last_bid_user',
        'active'
        ]

class UserProfileAdmin(admin.ModelAdmin):
    fields = ['user', 'premium', 'profile_pic', 'description',

        # Quelli tipicamente lasciati di default
        'sold_auction', 'feedback', 'auction_count', 'votes']

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Auction, AuctionAdmin)
admin.site.register(Vote)
admin.site.register(FollowedAuction)
