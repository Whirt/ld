# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from messenger.models import Message
from django.core.validators import MaxValueValidator, MinValueValidator

def MAX_AUCT_COUNT():
        return 3
def MAX_DESCRIPTION_LEN():
        return 1000
class UserProfile(models.Model):
    def __str__(self):
        return "UserProfile username" + self.name;

    # questo fa si' che a ogni creazione di User si crei anche questo
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            profile, created = UserProfile.objects.get_or_create(user=instance)
    post_save.connect(create_user_profile, sender=User)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    feedback = models.FloatField(default=0)
    # Per il sistema di feedback si ha sia il numero di sold_auction
    # che il numero di voti
    votes = models.IntegerField(default=0)
    auction_count = models.SmallIntegerField(default=3)
    premium = models.BooleanField(default=False)
    description = models.CharField(max_length=1000, default='')
    profile_pic = models.ImageField(upload_to='profile_img/',
                    default='profile_img/defaultprofileimage.png')
    sold_auction = models.IntegerField(default=0)
    # Quando un utente si discrive conviene disattivarlo e non cancellarlo dal db
    # per motivi statistici, user di django ha gia is_active!
    # basta settare questo a False successivamente

CATEGORY_CHOICES = (('MS','Music'), ('BK','Book'), ('CL','Clothes'), ('TL','Tools'),
    ('EL','Electronics'), ('GM','Games'), ('HS','House'), ('OT','Other'))

def MIN_BID():
    return 0.50
def MAX_DURATION_DAY():
    return 30
class Auction(models.Model):
    def __str__(self):
        return self.title
    # relazione ManyToOne
    seller = models.ForeignKey(User, related_name="seller", on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='auction_img/%Y/%m/%d/')
    description = models.CharField(max_length=5000)
    pub_date = models.DateTimeField(auto_now_add=True)
    # Il valore di default è il giorno stesso della pubbicazione
    # e svolge la funzione da segnalatore di errore
    expire_date = models.DateTimeField(default=datetime.datetime.now)
    min_price = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    # quantita' minima di offerta rispetto quello attuale
    min_bid = models.DecimalField(max_digits=10, default=MIN_BID(), decimal_places=2)
    # l'ultimo utente serve affinchè possa venire notificato
    # relazione ManyToOne e per far capire chi ha vinto, nel caso sia expired (active false)
    bid_count = models.IntegerField(default=0)
    last_bid_user = models.ForeignKey(User, null=True, related_name="last_bid_user", \
            on_delete=models.CASCADE)
    current_price = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    # active dice solo se non è scaduto, invece di fare un confronto di tempi
    active = models.BooleanField(default=True)
    category = models.CharField(max_length=50, default=('OT','Other'),
                                choices=CATEGORY_CHOICES)

def MAX_VOTE_LENGTH():
    return 1000;
class Vote(models.Model):
    def __str__(self):
        return self.message
    sender = models.ForeignKey(User, related_name="vote_sender", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="vote_receiver", on_delete=models.CASCADE)
    message = models.CharField(max_length=1000, blank=False)
    datetime = models.DateTimeField(auto_now_add=True)
    rating = models.SmallIntegerField(validators=[MaxValueValidator(5), MinValueValidator(1)])
