# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from django.contrib.auth.models import User

def MAX_MESSAGE_LENGTH():
        return 1000;
class Message(models.Model):
    def __str__(self):
        return "message beetween" + self.sender + "and" + self.receiver
    sender = models.ForeignKey(User, related_name="sender", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE)
    message = models.CharField(max_length=1000, blank=False)
    datetime = models.DateTimeField(auto_now_add=True)

""" FriendRequest è fatto modellato per funzionare in questa maniera:
1. Serve per capire se due utenti sono amici
2. Serve per capire anche la direzionalità della richiesta,
in friend_of ci sarà sempre colui che ha inviato la richiesta e in friend
colui che può accettarla
"""
class FriendRequest(models.Model):
    def __str__(self):
        return self.friend_of + "and" + self.friend + " friend request."
    friend_of = models.ForeignKey(User, related_name="friend_of", on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name="friend", on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    class Meta:
        unique_together=('friend_of','friend')
