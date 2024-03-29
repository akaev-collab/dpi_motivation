from st_pages import Page, show_pages

import hmac
import streamlit as st

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
    st.stop()  # Do not continue if check_password is not True.

st.text("Здесь будет инструкция для работы")


show_pages([Page("main.py","Главная","🙋‍♂️"),
            Page("calculation.py", "Калькулятор","🧮"),
            Page("dashboard.py", "Дашборд","🛫"),
            Page("fedback.py","Обратная связь","📬")])