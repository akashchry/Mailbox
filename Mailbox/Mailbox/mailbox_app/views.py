from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from django.http import HttpResponse
from django.utils import timezone

from .forms import RegisterForm
from .models import EmailHistory

import pandas as pd
import csv


# ==========================
# Home Page
# ==========================
@login_required(login_url='/login/')
def home(request):
    return render(request, "index.html")


# ==========================
# Register
# ==========================
def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect('/')

    else:

        form = RegisterForm()

    return render(
        request,
        "register.html",
        {"form": form}
    )


# ==========================
# Login
# ==========================
def login_view(request):

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            return redirect('/')

    else:

        form = AuthenticationForm()

    return render(
        request,
        "login.html",
        {"form": form}
    )


# ==========================
# Logout
# ==========================
def logout_view(request):

    logout(request)

    return redirect('/login/')


# ==========================
# History Dashboard
# ==========================
@login_required(login_url='/login/')
def history_view(request):

    emails = EmailHistory.objects.filter(
        user=request.user
    ).order_by('-sent_at')

    search = request.GET.get('search')

    if search:

        emails = emails.filter(
            recipient__icontains=search
        )

    filter_type = request.GET.get('filter')

    if filter_type == 'today':

        emails = emails.filter(
            sent_at__date=timezone.now().date()
        )

    total_emails = EmailHistory.objects.filter(
        user=request.user
    ).count()

    today_emails = EmailHistory.objects.filter(
        user=request.user,
        sent_at__date=timezone.now().date()
    ).count()

    total_users = User.objects.count()

    total_attachments = EmailHistory.objects.exclude(
        attachment=''
    ).count()

    return render(
        request,
        'history.html',
        {
            'emails': emails,
            'total_emails': total_emails,
            'today_emails': today_emails,
            'total_users': total_users,
            'total_attachments': total_attachments,
        }
    )


# ==========================
# Export CSV
# ==========================
@login_required(login_url='/login/')
def export_csv(request):

    response = HttpResponse(
        content_type='text/csv'
    )

    response[
        'Content-Disposition'
    ] = 'attachment; filename=history.csv'

    writer = csv.writer(response)

    writer.writerow([
        'Name',
        'Email',
        'Subject',
        'Status',
        'Date'
    ])

    emails = EmailHistory.objects.filter(
        user=request.user
    )

    for email in emails:

        writer.writerow([
            email.recipient_name,
            email.recipient,
            email.subject,
            email.status,
            email.sent_at
        ])

    return response


# ==========================
# Mailbox API
# ==========================
@method_decorator(login_required, name='dispatch')
class MailboxAPIView(APIView):

    def post(self, request):

        try:

            file = request.FILES.get("file")
            attachment = request.FILES.get("attachment")

            if not file:

                return Response({
                    "error":
                    "Please upload Excel/CSV file."
                })

            # Excel
            if file.name.endswith(".xlsx"):

                df = pd.read_excel(file)

            # CSV
            elif file.name.endswith(".csv"):

                df = pd.read_csv(file)

            else:

                return Response({
                    "error":
                    "Only CSV and Excel files are allowed."
                })

            required_columns = [
                "name",
                "email",
                "subject",
                "message"
            ]

            for column in required_columns:

                if column not in df.columns:

                    return Response({
                        "error":
                        f"Missing column: {column}"
                    })

            sent_count = 0

            for _, row in df.iterrows():

                name = str(
                    row["name"]
                ).strip()

                email = str(
                    row["email"]
                ).strip()

                subject = str(
                    row["subject"]
                ).strip()

                message = str(
                    row["message"]
                ).strip()

                html_content = render_to_string(
                    "email_template.html",
                    {
                        "name": name,
                        "message": message
                    }
                )

                email_message = EmailMultiAlternatives(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [email]
                )

                email_message.attach_alternative(
                    html_content,
                    "text/html"
                )

                if attachment:

                    attachment.seek(0)

                    email_message.attach(
                        attachment.name,
                        attachment.read(),
                        attachment.content_type
                    )

                email_message.send()

                history = EmailHistory.objects.create(
                    user=request.user,
                    recipient_name=name,
                    recipient=email,
                    subject=subject,
                    message=message,
                    status="Success"
                )

                if attachment:

                    history.attachment = attachment
                    history.save()

                sent_count += 1

            return Response({
                "message":
                f"{sent_count} emails sent successfully."
            })

        except Exception as e:

            return Response({
                "error": str(e)
            })