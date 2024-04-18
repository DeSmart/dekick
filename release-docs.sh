#!/bin/env bash
set -e

TMPDIR=$(mktemp -d)

if ! git diff --quiet --exit-code; then
  echo "There are uncommited changes. Please commit or stash them before releasing."
  exit 1
fi

echo "Building docs"
cd docs/docusaurus || exit 1
npm install
npm run build
mv build "$TMPDIR"
cd - || exit 1

git checkout docs
rm -rf ./*
mv "$TMPDIR"/build/* ./
git add .
git commit -m "docs: update"
git push origin docs

echo "Docs released!"
