# Thingsboard-HomematicIP Bridge



## Getting Started

Create virtual environment
```
C:\LocalData\Nextcloud\Tools\Python\python-3.7.2.amd64\python.exe -m venv .env
```

Activate virtual environment
```
.env\Scripts\activate
```

Install required packages
```
pip install -r requirements.txt
```

Register with HmIP Access Point
```
python .env\Scripts\hmip_generate_auth_token.py
```

Add Thingsboard configuration to config.ini
```ini
[TB]
url = >>>thingsboard url here<<<
rootDeviceId = >>>root deivce id here<<<
username = >>>username here<<<
password = >>>password here<<<
```

Run bridge
```
python ./src/main.py
```