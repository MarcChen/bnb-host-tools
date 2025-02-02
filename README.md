# template-repository
A template repository with branch protection and versioning pipeline

## How to use the setup.yml

Create a PAT (fine-grained)

1. Create a new fine-grained PAT
   In GitHub, go to Settings → Developer settings → Personal access tokens → Fine-grained tokens.
   Click Generate new token.
   Give it a Name (e.g., “Branch Protection + Label Creation Token”).
   Under Resource owner, select the repository owner (your personal account or an organization).
   Under Repositories, choose Only select repositories (if you want to limit it) or All repositories.
   If you choose only specific repos, select the one(s) where you need to create labels and configure branch protection.
   In Repository permissions:
   Set Issues to Read and write (needed to create/modify labels).
   Set Administration to Read and write (needed to configure branch protection).
   You can leave other permissions at No access, unless you want to allow more functionality.
   Click Generate token at the bottom.
   Copy the generated token and keep it safe—you will not be able to see it again.

2. Store the PAT as a secret in your repository
   In your GitHub repository, go to Settings → Secrets and variables → Actions → New repository secret.
   Name the secret something like PERSONAL_ACCESS_TOKEN.
   Paste your newly created PAT in the Secret field and click Save.

We need these two roles for PAT:
- Read access to metadata
- Read and Write access to administration and issues

## What setup.yml does

The `setup.yml` workflow is a one-time setup that performs the following actions:

1. Sets up the Node.js environment.
2. Creates labels for versioning (major, minor, patch).
3. Configures branch protection for the main branch.

