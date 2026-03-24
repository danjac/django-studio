**/dj-sync**

Pulls the latest django-studio template changes into this project via
`copier update` and helps resolve merge conflicts interactively.

Run this periodically to pick up new features, bug fixes, and skill updates
from the template. Runs `just check-all` after conflict resolution to verify
nothing is broken.

Example:
  /dj-sync
