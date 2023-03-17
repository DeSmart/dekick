# How to release Boilerplates?

1. Start a new release using git flow with the following command: 
```shell
git flow release start {VERSION}
```
2. Finish the release using the following command: 
```shell
git flow release finish {VERSION}
```
3. Push the tags using the command: 
```shell
git push --tags
```
4. Push all branches to the repository using the command:
```shell
git push --all
```

# How to release DeKick?

1. Start a new release using git flow with the following command:
```shell
git flow release start {VERSION}
```
2. Change the version in .version file from `develop` to `{VERSION}` ensure it matches our release. 
3. Generate images by navigating to the docker directory and running the following scripts: 
```shell
cd docker ./create-dekick-dind-image.sh && ./create-dekick-image.sh
```
4. Change the version in `README.md` file from `develop` to `{VERSION}`.

5. Add and commit changes using the below command:
```shell
git add .version README.md
git commit -m "chore: new version"
```
6. Finish the release using the following command: 
```shell
git flow release finish {VERSION}
```
7. Push the tags using the command: 
```shell
git push --tags
```
8. Push all branches to the repository using the command:
```shell
git push --all
```
9. Finally, go to the "releases" tab on GitHub and publish the release.
10. After that, on the develop branch, change version in `.version` `README.md` back to the `develop` commit changes.
