import streamlit as st
from src.frontend.config import ALLOW_DEV_BYPASS_GOOGLE_AUTH


def check_google_auth() -> bool:
    """
    Gère l'authentification via Google OIDC natif de Streamlit (st.login / st.user).
    Propose un mode démo en développement si .streamlit/secrets.toml n'est pas encore configuré.
    """
    # 1. Vérifier si l'utilisateur est déjà connecté via session_state (mode dev)
    if st.session_state.get("authenticated", False):
        return True

    # 2. Vérifier l'authentification native Google OIDC de Streamlit (>= 1.42)
    user_info = getattr(st, "user", None)
    if user_info is not None and getattr(user_info, "is_logged_in", False):
        st.session_state["authenticated"] = True
        st.session_state["user_email"] = getattr(user_info, "email", "Utilisateur Google")
        st.session_state["user_name"] = getattr(user_info, "name", "Utilisateur")
        return True

    # 3. Afficher l'écran de connexion
    st.markdown("## ✈️ Portail Liora Airlines — Connexion")
    st.info("Veuillez vous authentifier avec votre compte **Google** pour accéder à l'application.")

    col1, col2 = st.columns(2)
    st.write("Secrets chargés :", "auth" in st.secrets)
    with col1:
        if st.button("🔐 Se connecter avec Google", use_container_width=True, type="primary"):
            if hasattr(st, "login"):
                try:
                    st.login()
                except Exception as exc:
                    st.error(
                        "Configuration Google OAuth manquante ou invalide dans `.streamlit/secrets.toml`. "
                        f"Détail : {exc}"
                    )
            else:
                st.warning("Votre version de Streamlit est < 1.42. Mettez à jour Streamlit (`pip install -U streamlit Authlib`).")

    with col2:
        if ALLOW_DEV_BYPASS_GOOGLE_AUTH:
            if st.button("🧪 Connexion Google (Mode Démo Dev)", use_container_width=True):
                st.session_state["authenticated"] = True
                st.session_state["user_name"] = "Développeur DST"
                st.session_state["user_email"] = "dev@dst-airlines.local"
                st.rerun()

    return False


def render_user_sidebar() -> None:
    """Affiche les informations de l'utilisateur Google connecté et le bouton de déconnexion."""
    with st.sidebar:
        st.markdown("---")
        user_name = st.session_state.get("user_name", "Utilisateur")
        user_email = st.session_state.get("user_email", "")
        st.caption(f"👤 Connecté : **{user_name}**  \n`{user_email}`")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.clear()
            if hasattr(st, "logout"):
                try:
                    st.logout()
                except Exception:
                    pass
            st.rerun()
