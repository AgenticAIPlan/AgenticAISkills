#!/bin/sh
set -eu

repo_root="$(git rev-parse --show-toplevel)"

git config core.hooksPath "$repo_root/.githooks"
chmod +x "$repo_root/.githooks/pre-push"

echo "Installed repository hooks from $repo_root/.githooks"
echo "You can bypass local checks temporarily with SKIP_SKILLS_GUARD=1"
