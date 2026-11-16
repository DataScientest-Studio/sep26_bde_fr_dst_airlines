##################################################
# Test l'objet config
##################################################

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from spark.notebooks.common.config import Config

def create_fake_config(tmp_path:str)->str:
    """ Cree le fichier de config a tester """
    cfg_file = tmp_path / "config.json"

    cfg_file.write_text(
        json.dumps(
            {
                "PROJECT": "airline",
                "BUCKET": "my_bucket",
                "SECRETS_PREFIX": "projects/test/secrets/",
                "SECRETS": ["DB_PASSWORD"],
            }
        )
    )

    return cfg_file

def test_load_explicit_config_file(tmp_path):
    """
    Vérifie le chargement d'un fichier explicitement fourni.
    """

    # Cree le fichier de config a tester
    cfg_file = create_fake_config(tmp_path)

    cfg = Config(
        app_path="/tmp/my_script.py",
        config_file=str(cfg_file),
    )

    assert cfg["PROJECT"] == "airline"
    assert cfg.BUCKET == "my_bucket"


def test_getitem_and_setitem(tmp_path):
    """ Test le get et set de l'objet config """
    cfg_file = create_fake_config(tmp_path)

    cfg = Config(
        app_path="/tmp/my_script.py",
        config_file=str(cfg_file),
    )

    cfg["PROJECT"] = "new_project"

    assert cfg["PROJECT"] == "new_project"


def test_getattr_existing_key(tmp_path):
    """ Test la recuperation d'une variable et utilisant le nom config.ATTR """
    cfg_file = create_fake_config(tmp_path)

    
    cfg = Config(
        app_path="/tmp/my_script.py",
        config_file=str(cfg_file),
    )

    assert cfg.PROJECT == "airline"


def test_setattr_existing_key(tmp_path):
    """ Test l'affectation d'une variable config.VAR=... """
    cfg_file = create_fake_config(tmp_path)

    cfg = Config(
        app_path="/tmp/my_script.py",
        config_file=str(cfg_file),
    )

    cfg.PROJECT = "new_airline"

    assert cfg.PROJECT == "new_airline"


@patch("spark.notebooks.common.config.secretmanager.SecretManagerServiceClient")
def test_get_secrets(mock_client_class, tmp_path):
    cfg_file = create_fake_config(tmp_path)

    # Simule objet client
    mock_client = MagicMock()
    # simule objet response
    response = MagicMock()
    response.payload.data.decode.return_value = "secret_value"
    mock_client.access_secret_version.return_value = response
    mock_client_class.return_value = mock_client

    cfg = Config(
        app_path="/tmp/my_script.py",
        config_file=str(cfg_file),
    )
    # Appel get_secrets
    cfg.get_secrets()

    assert cfg.DB_PASSWORD == "secret_value"

    