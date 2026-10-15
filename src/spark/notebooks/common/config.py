import json, os
from google.cloud import secretmanager

class Config:

    def __init__(self,app_path:str, config_file:str=None):
        """ Initialise Configuration 
            @param app_path : Calling Script 
            @param config_file : Path to config file to use, None for using default in script folder
        """
        object.__setattr__(self, "config_content", {})
        app_name = os.path.basename(app_path)
        app_name = os.path.splitext(app_name)[0]
        app_path = os.path.dirname(app_path)
        if config_file is None:
            config_file = os.path.join(app_path, f"config_{app_name}.json")
            if not os.path.isfile(config_file):
                config_file = os.path.join(app_path, f"{app_name}.json")
            if not os.path.isfile(config_file):
                config_file = os.path.join(app_path, "config.json")
        
        r = os.path.isfile(config_file)        
        #if self.config_file is None or not os.path.isfile(self.config_file):
        #    raise Exception("No config file found")

        with open(config_file,"r") as fd:
            self.config_content = json.load(fd)

        

    def __getitem__(self, key):
        return self.config_content[key]

    def __setitem__(self, key, value):
        self.config_content[key] = value

    def __getattr__(self, name):
        try:
            
            if self.config_content and name in self.config_content:
                return self.config_content[name]
            else:
                object.__getattribute__(self, name)
        except KeyError:
            return None

    def __setattr__(self, name, value):
        if self.config_content is None: self.config_content={}
        if name in self.config_content:
            self.config_content[name] = value
        else:
            object.__setattr__(self, name, value)

    def get_secrets(self, secrets:list=None):
        if secrets is None and self.SECRETS is not None:
            secrets = self.SECRETS
        if secrets is None or self.SECRETS_PREFIX is None:
            return
        client = secretmanager.SecretManagerServiceClient()
        for secret in self.SECRETS:
            name = f"{self.SECRETS_PREFIX}{secret}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            value = response.payload.data.decode("UTF-8")
            self.config_content[secret] = value


