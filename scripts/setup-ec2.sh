#!/usr/bin/env bash
# One-time setup for the EC2 instance: installs Docker and lets your user run it.
# Usage (on the EC2 instance):  bash setup-ec2.sh
set -euo pipefail

if command -v dnf >/dev/null 2>&1; then
  echo "Amazon Linux detected - installing Docker with dnf"
  sudo dnf install -y docker
elif command -v apt-get >/dev/null 2>&1; then
  echo "Ubuntu/Debian detected - installing Docker with apt"
  sudo apt-get update -y
  sudo apt-get install -y docker.io
else
  echo "Unsupported OS. Install Docker manually: https://docs.docker.com/engine/install/" >&2
  exit 1
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

echo
echo "Docker installed: $(sudo docker --version)"
echo "Log out and SSH in again so '$USER' can run docker without sudo."
echo "Then test with:  docker run --rm hello-world"
