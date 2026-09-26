**/djs-scale [n]**

View or change the webapp replica count.

**No arguments** — prints the current replica count and Hetzner node count.

**With a number** — scales the deployment to that many replicas, warns about
downtime risks (0 or 1 replica), and offers to provision additional Hetzner
nodes if needed.

Examples:

```
/djs-scale          # show current replica count
/djs-scale 3        # scale to 3 replicas
/djs-scale 1        # scale down to 1 (warns about no redundancy)
```
