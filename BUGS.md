~~Ansible configuration completely broken, not processing files correctly:~~

~~HINT: only process Ansible files we need to, and ignore the rest.~~

**Resolved**: Fixed three issues:
1. `terraform/hetzner/variables.tf` had duplicate `description`/`type`/`default` in `cluster_name` block — removed stale duplicate
2. `terraform/hetzner/storage.tf` was a standalone module in the same dir as `variables.tf`, causing duplicate `variable "location"` — moved to `terraform/storage/main.tf`
3. `cookiecutter.json` `_copy_without_render` had `"ansible/**"` preventing `group_vars/all.yml` and `k3s_observability/defaults/main.yml` from being rendered — replaced with specific task/template/vars/defaults patterns; added `{% raw %}` guards to `group_vars/all.yml` for Ansible-specific variables
