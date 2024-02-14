import smtplib
from email.mime.text import MIMEText
import streamlit as st
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Пароль для входа", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False



if not check_password():
    st.stop()

def send_email(message):
    
    password = st.secrets["email_password"]["password"]
    
    sender = "samolet_st_collab@mail.ru"


    server = smtplib.SMTP_SSL("smtp.mail.ru", 465)

    try:
        server.login(sender, password)
     
        msg = MIMEText(message)
        
        server.sendmail(sender, sender, msg.as_string())
        #server.sendmail(sender,"dzhakhar.akaev@gmail.com", f"Subject: Python test\n{message}")

        return "The message was sent successfully!"
    
    except Exception as _ex:
        return f"{_ex}\nCheck your login or password please!"



from_email = st.text_input(":email: Укажите ваш email для обратноя связи")
from_phone = st.text_input(":telephone_receiver: Укажите номер телефона для обратноя связи")
from_telegram = st.text_input(":bell: Укажите ваш аккаунт Telegram для  обратной связи")
body = st.text_area(":newspaper: Отзыв")

text = f"Отправитель: {from_email}\nКонтатный номер телефона: {from_phone}\nТелеграмм: {from_telegram}\nОтзыв: {body}"
 
if st.button("Отправить"):
    send_email(text)
    st.success("Письмо отправлено!", icon="✅")