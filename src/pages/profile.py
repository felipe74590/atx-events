import streamlit as st

st.write("My profile")


def register_user(user_name, password, email):
    """Register a user into the database."""


def login_user(user_name, password):
    """Login user into app."""


# Create tabs for registration and login
tab1, tab2 = st.tabs(["Register", "Login"])
with tab1:
    st.header("Register")
    reg_username = st.text_input("Username", key="reg_username")
    reg_password = st.text_input("Password", type="password", key="reg_password")
    reg_email = st.text_input("Email")

    if st.button("Register"):
        register_user(reg_username, reg_password, reg_email)

with tab2:
    st.header("Login")
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        login_user(login_username, login_password)
