c = get_config()

# --------------------------------------------------
# JupyterHub
# --------------------------------------------------

c.JupyterHub.bind_url = "http://0.0.0.0:8888"


# --------------------------------------------------
# Authentification
# --------------------------------------------------

# Utilise les comptes Linux du conteneur
c.JupyterHub.authenticator_class = "pam"

# Seuls ces utilisateurs peuvent se connecter
c.Authenticator.allowed_users = {
    "herve_cyr",
    "pascal",
}

# Administrateur JupyterHub
c.Authenticator.admin_users = {
    "herve_cyr",
}


# --------------------------------------------------
# JupyterLab
# --------------------------------------------------

# Même workspace pour tous
c.Spawner.notebook_dir = "/home/jovyan/work"

# Démarrer directement JupyterLab
c.Spawner.default_url = "/lab"

# Délai de démarrage
c.Spawner.start_timeout = 60