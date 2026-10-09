FROM quay.io/jupyter/pyspark-notebook

# ------------------------------------------------
# Packages Python utilisés par les notebooks
# ------------------------------------------------
USER root

# connector pour Google storage
RUN wget -O \
  /opt/conda/lib/python3.13/site-packages/pyspark/jars/gcs-connector.jar \
  https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-hadoop3-latest.jar

USER ${NB_UID}

RUN pip install --no-cache-dir \
  google-cloud-storage \
  sqlalchemy \
  psycopg2-binary \
  jupyterhub \
  google-cloud-secret-manager \
  pyspark

USER root

# JupyterHub proxy
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    npm install -g configurable-http-proxy && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------
# Configuration multi-utilisateur
# ------------------------------------------------
USER root

# Groupe commun
RUN if getent group project-team > /dev/null; then \
        groupmod -g 1005 project-team; \
    else \
        groupadd -g 1005 project-team; \
    fi

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
RUN chgrp project-team /home/jovyan && \
    chmod 2770 /home/jovyan

# Le conteneur doit démarrer en root pour pouvoir exécuter chpasswd
USER root

CMD ["/usr/local/bin/start-jupyterhub.sh"]