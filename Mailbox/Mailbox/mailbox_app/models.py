from django.db import models
from django.contrib.auth.models import User


class EmailHistory(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # New Field
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    recipient = models.EmailField()

    subject = models.CharField(
        max_length=255
    )

    message = models.TextField()

    attachment = models.FileField(
        upload_to='attachments/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.recipient