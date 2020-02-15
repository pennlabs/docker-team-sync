import os

import hvac
from jinja2 import Template


def sync(teams):
    client = hvac.Client(url=os.getenv("VAULT_ADDR"))
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
            jwt = f.read()
            client.auth_kubernetes("team-auth", jwt)
    except FileNotFoundError:
        print("vault: Could access service account token. Exiting.")
        return

    if not client.sys.is_sealed():
        with open("sync/modules/user-policy.hcl.j2") as f:
            t = Template(f.read())
            for team in teams["leads"]:
                base_team_slug = team.slug.replace("-leads", "")
                pol = t.render(team_name=base_team_slug)
                client.sys.create_or_update_policy(name=base_team_slug, policy=pol)
                client.auth.github.map_team(team_name=team.slug, policies=[base_team_slug])
    else:
        print("vault: Vault sealed. Stopping.")
