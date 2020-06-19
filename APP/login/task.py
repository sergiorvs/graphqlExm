from django.core.mail import EmailMessage

from celery import shared_task


@shared_task
def send_email(**kwargs):
    _email = kwargs.get('email')
    mail_subject = kwargs.get('subject')
    message = kwargs.get('message')

    email = EmailMessage(
        mail_subject,
        message, to=[_email])
    email.send()
    print('Mail Sended!')
