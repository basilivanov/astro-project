#!/bin/bash
set -euo pipefail

# Ensure workloop talks to the astro instance (not other Ductor services)
export DUCTOR_INTERAGENT_PORT=${DUCTOR_INTERAGENT_PORT:-8800}
export DUCTOR_AGENT_NAME=${DUCTOR_AGENT_NAME:-astro}
export DUCTOR_CHAT_ID=${DUCTOR_CHAT_ID:-833478509}

cd /opt/astro-project
/usr/bin/env python3 astro_workloop.py --max-running 2
