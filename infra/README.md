# Infra GCP (Terraform)

Terraform **exporté depuis GCP** : le code décrit l'infra existante, il ne la crée pas depuis zéro.
Les blocs `import {}` de [imports.tf](imports.tf) rattachent les ressources déjà présentes.

```
infra/
├── main.tf, providers.tf, variables.tf, terraform.tfvars   # racine
├── secret_manager.tf   # secrets + accès (les VALEURS ne sont pas gérées ici)
├── firewall.tf         # règles du réseau "default"
├── imports.tf          # rattachement des ressources existantes (supprimable après un apply)
└── modules/{vm,cloud_run,scheduler}/
```

## Commandes utiles (et pièges)

```bash
# 1. Initialiser SANS état distant (il n'y a pas de backend configuré)
terraform init -backend=false

# 2. Vérifier la syntaxe et la cohérence : n'appelle PAS GCP
terraform fmt -recursive -check
terraform validate

# 3. Comparer le code avec le vrai GCP : LECTURE SEULE, ne modifie rien
terraform plan -input=false -lock=false
```

Ce qui est spécifique à ce projet :

- **`-backend=false`** : pas de backend, donc l'état est local (`terraform.tfstate`, ignoré par git, il peut
  contenir des secrets). Pour travailler à plusieurs il faudra un bucket GCS.
- **Lire le plan, pas seulement la dernière ligne.** Cherchez `must be replaced` / `forces replacement` :
  la VM serait détruite et recréée. Le résultat attendu aujourd'hui est
  `Plan: 15 to import, 0 to add, 0 to change, 0 to destroy`.
- **Premier `apply`** : il ne fait que les imports (rien n'est modifié dans GCP tant que le plan montre
  0 add/change/destroy). Relisez toujours le plan avant de taper `yes`.
- **`terraform destroy` est volontairement difficile** : Cloud Run a `deletion_protection` à true par défaut.
- **Ne jamais utiliser `-target`** pour "aller plus vite" : on contourne les dépendances (le scheduler lit le
  nom de la VM via `module.vm`).
- **Jamais de `-auto-approve`** sur cette infra importée.
- **Identifiants** : Terraform utilise les *Application Default Credentials*
  (`gcloud auth application-default login`), pas le `gcloud auth login` classique : ce sont deux sessions distinctes.
  `GOOGLE_APPLICATION_CREDENTIALS` peut pointer vers un autre fichier d'identifiants.
- **Windows + Avast** : Terraform plante avec `x509: certificate signed by unknown authority` (échec TLS entre
  Terraform et son plugin), et `gcloud` avec `CERTIFICATE_VERIFY_FAILED`. Contournement : lancer Terraform
  depuis **WSL**, ou désactiver temporairement le « Web Shield » d'Avast.
- **Commiter `.terraform.lock.hcl`** (versions du provider), mais jamais `.terraform/` ni `*.tfstate`.

## Ce que Terraform ne gère volontairement PAS

| Élément | Pourquoi |
| --- | --- |
| Valeurs des secrets | éviter qu'elles se retrouvent en clair dans le state |
| Clés SSH de la VM | gérées dans GCP (`ignore_changes` sur `metadata`) |
| Image Cloud Run | déployée par GitHub Actions (`ignore_changes`) |
| Rôles du compte de service (`compute.instanceAdmin`, `run.invoker`…) | non exportés, à ajouter si besoin |

## Points de sécurité à traiter

- Ports **22 (SSH)** et **3389 (RDP)** ouverts à `0.0.0.0/0` dans [firewall.tf](firewall.tf). RDP est inutile sur Debian.
- Ne jamais donner `run.invoker` à `allUsers` sur le service Cloud Run (quota AirLabs payant).
