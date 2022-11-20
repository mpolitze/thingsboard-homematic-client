# Thingsboard-HomematicIP Bridge

Pull changes from Homematic IP Access Point / Cloud and push them into Thingsboard via REST API.

The latest build is avialable as a container running a cron job to push the values every 10 minutes.

If you need more freuquent updates you have to modify the crontab in the container or build your own image. Please be gentile to the Homematic IP API!

## Setup with container

1. Follow steps below to create a working `config.ini`
2. Create a volume to store the config `podman volume create thingsboard-homematic-client-config`
3. Copy the contents of the `config.ini` to the volume `podman run -it --rm -v thingsboard-homematic-client-config:/config ghcr.io/mpolitze/thingsboard-homematic-client:latest vi /config/config.ini`
4. Run the container as deamon `podman run -d --name thingsboard-homematic-client -v thingsboard-homematic-client-config:/config ghcr.io/mpolitze/thingsboard-homematic-client:latest`

## Development

You can run the bridge in a local virtual environment, in a standard python container or use the lates released container image from `ghcr.io/mpolitze/thingsboard-homematic-client:latest`. Setup for virtual environment is below.

### Run development container

```sh
podman run -it --rm -v${PWD}:/root/src python:alpine /bin/sh
```

### Create virtual environment

```sh
python3 -m venv .env
```

### Activate virtual environment

(Windows)
```sh
.env\Scripts\activate
```

(Linux)
```sh
source .env/bin/activate
```

### Install required packages

(Build dependencies for alpine)
```sh
apk add --update --no-cache --virtual .build-deps gcc musl-dev git
```

```sh
pip3 install -r requirements.txt
```

### Register with HmIP Access Point

```sh
python3 .env/Scripts/hmip_generate_auth_token.py
```

### Add Thingsboard configuration to config.ini

```ini
[TB]
url = >>>thingsboard url here<<<
rootDeviceId = >>>root deivce id here<<<
username = >>>username here<<<
password = >>>password here<<<
```

### Run bridge
```sh
python3 ./src/main.py
```