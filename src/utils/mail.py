#!/usr/bin/env python
import os
import configparser
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from utils import *
logger = log_manager.get_logger(__name__)


####################################-SENDING EMAILS CONTAINING EBOOK-############################################
COMMA = ", "
DEFAULT_BODY = "Enjoy!"
DEFAULT_SUBJECT = "New free packt ebook"

class MailBook:

    def __init__(self, cfgFilePath):
        myDefaults = {'fromEmail': None,'toEmails': [],'kindleEmails': None, }
        config = configparser.ConfigParser(defaults=myDefaults)
        config.read(cfgFilePath)
        try:
            self._smtp_host = config.get("MAIL", 'host')
            self._smtp_port = config.get("MAIL", 'port')
            self._email_pass = config.get("MAIL", 'password')
            self._send_from = config.get("MAIL", 'email')
            self._to_emails = config.get("MAIL", 'toEmails').split(COMMA)
            self._kindle_emails = config.get("MAIL", 'kindleEmails').split(COMMA)
        except configparser.NoSectionError:
            raise ValueError("ERROR: need at least one from and one or more to emails")
    
    def _create_email_msg(self, to=None, subject=None, body=None):
        msg = MIMEMultipart()
        msg['From'] = self._send_from
        if to:
            self._to_emails = to
        msg['To'] = COMMASPACE.join(self._to_emails)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        body = body if body else DEFAULT_BODY
        msg.attach(MIMEText(body))   
        return msg
    
    def _send_email(self, msg):
        try:
            smtp = smtplib.SMTP(host=self._smtp_host, port=self._smtp_port)
            smtp.connect(host=self._smtp_host, port=self._smtp_port)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self._send_from, self._email_pass)
            logger.info('Sending email from {} to {} ...'.format(self._send_from, ','.join(self._to_emails)))
            smtp.sendmail(self._send_from, self._to_emails, msg.as_string())
            logger.info('Email to {} has been succesfully sent'.format(','.join(self._to_emails)))
        except Exception as e:
            logger.error('Sending failed with an error: {}'.format(str(e)))
        finally:
            smtp.quit()
    
    def send_info(self, subject="Info message from packtPublishingFreeEbook.py script", body=None):
        msg = self._create_email_msg(subject=subject, body=body)
        self._send_email(msg)
    
    def send_book(self, book, to=None):
        if not os.path.isfile(book):
            raise ValueError("ERROR: {} file doesn't exist.".format(book))
        book_name = basename(book)
        subject = "{}: {}".format(DEFAULT_SUBJECT, book_name)
        msg = self._create_email_msg(to, subject=subject)
        with open(book, "rb") as f:
            part = MIMEApplication(
                f.read(),
                Name=book_name
            )
            part['Content-Disposition'] = 'attachment; filename="{}"'.format(book_name)
            msg.attach(part)
        logger.info('Sending ebook: {} ...'.format(book_name))
        self._send_email(msg)

    def send_kindle(self, book):
        if not self._kindle_emails:
            return
        self.send_book(book, to=self._kindle_emails) 

