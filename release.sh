#!/bin/env bash
set -e

VERSION="$1"
CURRENT_VERSION=$(wget -qO- https://raw.githubusercontent.com/DeSmart/dekick/main/.version)
BOILERPLATES_DIR=boilerplates/

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

if [[ $(echo -e "$VERSION\n$CURRENT_VERSION" | sort -Vr | head -n 1) != "$VERSION" ]] || [ "$VERSION" = "$CURRENT_VERSION" ]; then
  echo "Error: VERSION must be greater than CURRENT_VERSION"
  exit 1
fi

git flow init -d

echo "Releasing version $VERSION"

read -p "Continue? (y/n) " -n 1 -r
if [[ $REPLY =~ ^[Nn]$ ]]; then
  exit 1
fi


echo "Releasing boilerplates"
cd "$BOILERPLATES_DIR" || exit 1

git flow release start "${VERSION}"
git flow release finish "${VERSION}" -m "chore: tag"
git push --tags
git push --all
cd - || exit 1

echo "Releasing DeKick"
git flow release start "${VERSION}"

echo "Saving version to .version"
echo -n "$VERSION" > .version
git add .version
git commit -m "chore: new version"

echo "Changing README.md"
sed -i "s/version-develop-teal/version-$VERSION-teal/g" README.md || true
sed -i "s/\[version-develop\]/[version-$VERSION]/g" README.md || true
git add README.md || true
git commit -m "docs: update" || true

echo "Creating Docker images"
cd docker || exit 1
./create-dekick-dind-image.sh
./create-dekick-image.sh
cd - || exit 1

git checkout .
git checkout main
git pull
git checkout "release/${VERSION}"
git flow release finish "${VERSION}" -m "chore: tag"
git push --tags
git push --all

echo "Version released!"

echo "Switching back to develop branch"
git checkout develop

echo -n "develop" > .version
git add .version
git commit -m "chore: new version"

echo "Changing README.md"
sed -i "s/version-$VERSION-teal/version-develop-teal/g" README.md
sed -i "s/\[version-$VERSION\]/[version-develop]/g" README.md
git add README.md
git commit -m "docs: update"

echo "Creating Docker images"
cd docker || exit 1
./create-dekick-dind-image.sh
./create-dekick-image.sh

cd - || exit 1
git push --tags
git push --all

echo "Version $VERSION released!"
