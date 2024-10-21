import streamlit as st
import requests
from constants import EVENTS_API_URL

st.write("My profile")


def register_user(user_name, password, email):
    """Register a user into the database."""
    data = {"user_name": user_name, "email": email, "password": password}
    registration_response = requests.post(EVENTS_API_URL + "/users/", json=data)
    if registration_response.status_code == 409:
        st.error("User already exists.")
    else:
        st.success("User registered successfully.")
    return registration_response.json()


def login_user(user_name, password):
    """Login user into app."""
    data = {"username": user_name, "password": password}
    login_response = requests.post(EVENTS_API_URL + "/token", data=data)
    print("Response Status:", login_response.status_code)
    print("Response Content:", login_response.text)
    if login_response.status_code == 200:
        return login_response.json()
    else:
        st.error("Incorrect username or password.")
        return None


def get_user_details(token):
    """Return user details of loggedin User."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(EVENTS_API_URL + "/users/me/", headers=headers)
    return response.json() if response.status_code == 200 else None


# Create tabs for registration and login
tab1, tab2 = st.tabs(["Register", "Login"])
with tab1:
    st.header("Register")
    if "registered" in st.session_state and st.session_state["registered"]:
        st.success("Registration succesful, you can now login!")
    else:
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_email = st.text_input("Email")

        if st.button("Register"):
            if register_user(reg_username, reg_password, reg_email):
                st.session_state["registered"] = True


with tab2:
    st.header("Login")
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        token_data = login_user(login_username, login_password)

        if token_data:
            token = token_data["access_token"]
            st.session_state.token = token

            user_details = get_user_details(token)
            if user_details:
                st.session_state.user_details = user_details
                st.session_state["logged_in"] = True
                st.success(f"Logged in as {user_details['user_name']}")
