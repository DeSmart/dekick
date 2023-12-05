# How to release Boilerplates?

- Start a new release using git flow with the following command: 
```shell
git flow release start {VERSION}
```
- Finish the release using the following command: 
```shell
git flow release finish {VERSION}
```
- Push the tags using the command: 
```shell
git push --tags
```
- Push all branches to the repository using the command:
```shell
git push --all
```

# How to release DeKick?

- Start a new release using git flow with the following command:
```shell
git flow release start {VERSION}
```
- Change the version in `.version` file from `develop` to `{VERSION}` ensure it matches our release. 
- Generate Docker images by navigating to the `docker/` directory and running the following scripts: 
```shell
cd docker; ./create-dekick-dind-image.sh && ./create-dekick-image.sh
```
- Change the version in `README.md` file from `develop` to `{VERSION}`.
- Add and commit changes using the below command:
```shell
git add .version README.md
git commit -m "chore: new version"
```
- Finish the release using the following command: 
```shell
git flow release finish {VERSION}
```
- Push the tags using the command: 
```shell
git push --tags
```
- Push all branches to the repository using the command:
```shell
git push --all
```
- Go to the "releases" tab on GitHub and publish the release.
- On `develop` branch, change version in `.version` `README.md` back to the `develop`. Commit changes.
- Generate images for `develop` version by navigating to the docker directory and running the following scripts: 
```shell
cd docker; ./create-dekick-dind-image.sh && ./create-dekick-image.sh
```