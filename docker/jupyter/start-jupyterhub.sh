#!/bin/bash
set -e

echo "herve_cyr:${JUPYTER_PASSWORD_HERVE}" | chpasswd
echo "pascal:${JUPYTER_PASSWORD_PASCAL}" | chpasswd

exec jupyterhub -f /etc/jupyterhub/jupyterhub_config.py