import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app


class NotificationService:
    @staticmethod
    def send_email(to_address, subject, text_body, html_body=None, plain_body=None):
        mail_host = current_app.config.get('MAIL_HOST')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        mail_user = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_from = current_app.config.get('MAIL_DEFAULT_SENDER') or mail_user
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        use_ssl = current_app.config.get('MAIL_USE_SSL', False)

        if not mail_host or not mail_user or not mail_password or not mail_from:
            current_app.logger.warning(
                '邮件配置不完整，无法发送通知：MAIL_HOST=%s MAIL_USERNAME=%s MAIL_PASSWORD=%s MAIL_DEFAULT_SENDER=%s',
                mail_host, mail_user, bool(mail_password), mail_from
            )
            return False

        if plain_body is None:
            plain_body = text_body

        if html_body is None:
            html_content = html.escape(text_body).replace('\n', '<br>')
        else:
            html_content = html_body

        message = MIMEMultipart('alternative')
        message['From'] = mail_from
        message['To'] = to_address
        message['Subject'] = subject
        message.attach(MIMEText(plain_body, 'plain', 'utf-8'))
        message.attach(MIMEText(html_content, 'html', 'utf-8'))

        try:
            if use_ssl:
                smtp = smtplib.SMTP_SSL(mail_host, mail_port, timeout=15)
            else:
                smtp = smtplib.SMTP(mail_host, mail_port, timeout=15)
                if use_tls:
                    smtp.starttls()

            smtp.login(mail_user, mail_password)
            smtp.sendmail(mail_from, [to_address], message.as_string())
            smtp.quit()
            current_app.logger.info('通知邮件已发送：%s -> %s', mail_from, to_address)
            return True
        except Exception as ex:
            current_app.logger.exception('发送邮件失败：%s', ex)
            return False

    @staticmethod
    def notify_user(user, subject, body):
        if user.email:
            return NotificationService.send_email(user.email, subject, body)

        current_app.logger.info(
            '用户 %s (%s) 未配置邮箱，通知内容已记录：%s',
            user.id,
            getattr(user, 'username', 'unknown'),
            subject
        )
        return False
