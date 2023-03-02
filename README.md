# What's DeKick?
DeKick /də kɪk/ is a tool which supports and improves the work of dev team, by provisioning and building unified environments using [Docker](https://docker.com) without being an expert. It relieves the pain of running projects locally on different platforms (Linux, macOS with Intel and ARM based CPUs) and prevents many common problems faced by developers when dockerizing their projects.

DeKick goes even further and helps to build target Docker images which can be deployed on a test, beta or even production environment with ease.

Therefore, it helps to reduce the time spent on setting up and configuring development environments and enables developers to quickly switch between projects or work on multiple projects simultaneously without any compatibility issues.

## What is our goal?
Transform the way developers work, giving them the freedom to run apps, ignite their coding passion, and bring their projects to life with effortless fixes and deployments.

## Common problems DeKick can help with:
- Differences in local environments between members of the same team, cause many additional issues. 
- What worked locally doesn't work in other environments e.g. test, beta or production. 
- Using Docker and dockerizing software needs additional knowledge.
- The need for assistance when a new developer approaches the project for the first time.  
- Revisiting a project from years past, eager to make a small adjustment, only to be met with the frustration of being unable to launch it.
- The burden of installing numerous required software, including the correct versions of Node and PHP, along with additional software, and the hassle of setting it all up.
- The inconsistency in platforms used by dev team members, e.g. one using macOS with Apple M1 processor and the other using a unique Linux distribution, creating difficulties in installing required software and intensifying platform differences.
- Hardware failures exclude a developer from work for a significant period.

## How DeKick helps your team?
DeKick can be the answer when ***"It (locally) works for me"*** is not enough ;) It:

- Maintains consistency between team members' local setups and target environments.
- Allows you to run a project on a computer that has almost nothing on it, runs in dockerized environment as well, so it requires only Docker to operate and making it easy and fast to start (in minutes).
- Allows people who are not proficient in Docker commands to take advantage of the dockerized project.
- Eases onboarding for new team members and reduces dependence on senior developers.
- Simplifies switching between projects with varying environment requirements. Work on multiple projects or revisit old ones seamlessly, without the need for constant local environment adjustments.
- Uses built in boilerplates to create basic file structure needed to quickly start your project, at the same time bringing standardization.
- Starts local database and seeds it with pre-set data (as specified by the chosen flavour)
- Runs backend and frontend simultaneously, at the same device, even if using different versions of, e.g. Node.

# Getting started
## System requirements

- Linux / macOS, both Intel and ARM CPUs are supported
- Docker on Linux and/or Docker Desktop on macOS installed
- Terminal with `bash` or `zsh` shell

## Usage

…that's it 🙂 Happy DeKicking!

# This project is still under development
More documentation will be available soon.

# Contribution
## Troubleshooting

### docker permission denied

If you get an error similar to this:

```shell
docker: Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Post http://%2Fvar%2Frun%2Fdocker.sock/v1.35/containers/create: dial unix /var/run/docker.sock: connect: permission denied. See 'docker run --help'.
```

It means that `docker` does not have correct permissions to run. DeKick expects that you are [managing docker as a non-root user][1] by adding it to the `docker` unix group. To create the docker group and add your user:

```shell
# Create the docker group.
sudo groupadd docker
# Add your user to the docker group.
sudo usermod -aG docker $USER
```

Please refer to [post-installation steps][1] and [troubleshooting][2] sections of the Docker documentation for more details.

If you want to contribute, please email dooshek@desmart.com

# Licence:
MIT
[1]: https://docs.docker.com/engine/install/linux-postinstall/
[2]: https://docs.docker.com/engine/install/troubleshoot/
