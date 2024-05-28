#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset




case "${1}" in
    "backend")
        shift
        echo "Starting Inference..."
        set -o errexit
        set -o pipefail
        set -o nounset

        python main.py
        ;;
    "worker")
        shift
        echo "Starting Worker ..."
        set -o errexit
        set -o pipefail
        set -o nounset

        exec celery -A celery_app worker -l INFO --concurrency 10 #-c 1 -P solo
        ;;
    "beat")
        shift
        echo "Starting Producer ..."
        set -o errexit
        set -o pipefail
        set -o nounset

        exec celery -A celery_app beat -l INFO
        ;;
    "pytest")
        shift
        echo "Tests"
        # shellcheck disable=SC2068
        exec pytest ${@}
        ;;
    *)
        # shellcheck disable=SC2068
        exec ${@}
        ;;
esac
