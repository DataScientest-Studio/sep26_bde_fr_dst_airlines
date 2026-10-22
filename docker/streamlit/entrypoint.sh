#!/bin/sh
set -eu

mkdir -p /root/.streamlit
rm -rf /root/.streamlit/secrets.toml
cat > /root/.streamlit/secrets.toml <<EOF
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "${COOKIE_SECRET}"
client_id = "${GOOGLE_CLIENT_ID}"
client_secret = "${GOOGLE_CLIENT_SECRET}"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
EOF

exec python -m streamlit run app.py \
    --server.address=0.0.0.0 \
    --server.port=8501