# How to release DeKick? #

1. Start a new release using git flow with the following command: 
```shell
git flow release start {VERSION}
```
2. Check the version in .version file to ensure it matches our release. 
3. Generate images by navigating to the docker directory and running the following scripts: 
```shell
cd docker ./create-dekick-dind-image.sh && ./create-dekick-image.sh
```
4. Update the version number in the file below to the current version. 
`README.md`
5. Add changes using the below command:
```shell
git add {FILE}
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
10.  After that, on the develop branch, determine the next release version in below files so that it is the next sequential version and commit changes:
`.version`,
`README.md`
11. Generate images for new version by navigating to the docker directory and running the following scripts: 
```shell
cd docker ./create-dekick-dind-image.sh && ./create-dekick-image.sh
```
12. In the `boilerplates` repository, create a new release branch from the previous one, using the below command with the next `DeKick version`:
```shell
git checkout -b release/{VERSION}
```
