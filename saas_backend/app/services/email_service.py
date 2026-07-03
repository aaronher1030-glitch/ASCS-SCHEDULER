import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_otp_email(to_email: str, otp_code: str):
    """
    Sends an OTP code via Gmail. 
    If GMAIL_USER or GMAIL_APP_PASSWORD are not set, it prints to the console (for prototyping).
    """
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    # Prototyping fallback: If no email credentials, just print it.
    if not gmail_user or not gmail_password:
        print("\n" + "="*50)
        print("🚨 PROTOTYPE MODE: NO GMAIL CREDENTIALS FOUND 🚨")
        print(f"OTP generated for {to_email}: {otp_code}")
        print("="*50 + "\n")
        return

    # Real sending via smtplib
    subject = "Your ASCS Login Code"
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #0038A8;">Automated Class Scheduling System</h2>
        <p>Your one-time login code is:</p>
        <h1 style="font-size: 32px; letter-spacing: 5px; color: #CE1126;">{otp_code}</h1>
        <p>If you did not request this code, please ignore this email.</p>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()
        print(f"OTP email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        # Fallback to console print if sending fails so dev doesn't get locked out
        print(f"OTP for {to_email}: {otp_code}")
