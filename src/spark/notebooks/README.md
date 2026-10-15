# Debug en local :
- VS Code
- Installer Java SDK 17
- Definir les variables d'environnement
  
  Postscript:
```
[System.Environment]::SetEnvironmentVariable("JAVA_HOME","C:\Program Files\Java\jdk-17","User")

[System.Environment]::SetEnvironmentVariable("PATH",$env:PATH + ";$env:JAVA_HOME\bin","User")
```
- Installer les packages python
```
pip install --no-cache-dir pandas numpy scikit-learn  xgboost  mlflow google-cloud-storage google-cloud-secret-manager pyarrow requests debugpy pyspark
```
- Installer gcloud
     ```
     (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
     & $env:Temp\GoogleCloudSDKInstaller.exe
     ```
- Authentifier gcloud
    ```
    gcloud auth application-default login
    ```