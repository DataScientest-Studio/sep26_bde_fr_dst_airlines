FROM quay.io/jupyter/pyspark-notebook

# ------------------------------------------------
# Packages Python utilisés par les notebooks
# ------------------------------------------------
USER ${NB_UID}

RUN pip install --no-cache-dir \
  google-cloud-storage \
  sqlalchemy \
  psycopg2-binary \
  jupyterhub


# ------------------------------------------------
# Configuration multi-utilisateur
# ------------------------------------------------
USER root

# Groupe commun
RUN groupadd -f project-team

# Utilisateurs
RUN useradd -m -s /bin/bash herve_cyr && \
    useradd -m -s /bin/bash pascal 

# Groupe commun
RUN usermod -aG project-team herve_cyr && \
    usermod -aG project-team pascal && \
    usermod -aG project-team ${NB_USER}

# Configuration JupyterHub
COPY docker/jupyter/jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py

# Script de démarrage
COPY docker/jupyter/start-jupyterhub.sh /usr/local/bin/start-jupyterhub.sh
RUN chmod +x /usr/local/bin/start-jupyterhub.sh

WORKDIR /home/jovyan/work

# Le conteneur doit démarrer en root pour pouvoir exécuter chpasswd
USER root

CMD ["/usr/local/bin/start-jupyterhub.sh"]