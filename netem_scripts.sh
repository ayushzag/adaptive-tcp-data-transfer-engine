#!/usr/bin/env bash

set -euo pipefail


# ============================================================
# Configuration
# ============================================================

IFACE="${IFACE:-lo}"


# ============================================================
# Helpers
# ============================================================

require_tc() {

    if ! command -v tc >/dev/null 2>&1; then

        echo "ERROR: 'tc' command not found."

        echo
        echo "tc/netem is a Linux networking tool."
        echo "Run this script inside Linux"
        echo "(VM / Linux environment / container setup)."

        exit 1
    fi
}


apply_delay() {

    echo "Applying:"
    echo "  delay = 50ms"
    echo "  jitter = 10ms"
    echo

    sudo tc qdisc replace \
        dev "$IFACE" \
        root netem \
        delay 50ms 10ms

    echo "Applied delay impairment."
}


apply_loss() {

    echo "Applying:"
    echo "  packet loss = 1%"
    echo

    sudo tc qdisc replace \
        dev "$IFACE" \
        root netem \
        loss 1%

    echo "Applied packet-loss impairment."
}


apply_delay_loss() {

    echo "Applying:"
    echo "  delay = 50ms"
    echo "  jitter = 10ms"
    echo "  packet loss = 1%"
    echo

    sudo tc qdisc replace \
        dev "$IFACE" \
        root netem \
        delay 50ms 10ms \
        loss 1%

    echo "Applied delay + loss impairment."
}


show_qdisc() {

    echo "Current qdisc configuration:"
    echo

    sudo tc qdisc show dev "$IFACE"
}


clear_qdisc() {

    echo "Removing netem configuration..."

    sudo tc qdisc del \
        dev "$IFACE" \
        root 2>/dev/null || true

    echo "Netem configuration cleared."
}


# ============================================================
# Main
# ============================================================

require_tc


ACTION="${1:-show}"


case "$ACTION" in

    delay)

        apply_delay
        ;;

    loss)

        apply_loss
        ;;

    delay_loss)

        apply_delay_loss
        ;;

    show)

        show_qdisc
        ;;

    clear)

        clear_qdisc
        ;;

    *)

        echo "Usage:"
        echo
        echo "  ./netem_scripts.sh delay"
        echo "  ./netem_scripts.sh loss"
        echo "  ./netem_scripts.sh delay_loss"
        echo "  ./netem_scripts.sh show"
        echo "  ./netem_scripts.sh clear"
        echo
        echo "Optional interface:"
        echo
        echo "  IFACE=eth0 ./netem_scripts.sh delay"

        exit 1
        ;;

esac