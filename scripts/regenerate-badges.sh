#!/usr/bin/env bash

set -e

if [[ -f .coverage ]]; then
  percent_covered_display=$(poetry run -- coverage json --include "src/*" -o - | jq -r '.totals.percent_covered_display')
#  echo "Running pytest covers $percent_covered_display% of the source files."
  echo "Generating coverage badge.."
  poetry run -- python -m pybadges --left-text=coverage --right-text="$percent_covered_display%" > images/coverage.svg
else
  >&2 echo "No coverage report found. Skipping regeneration of coverage badge."
fi
