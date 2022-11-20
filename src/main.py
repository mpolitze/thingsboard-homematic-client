import homematicip
from homematicip.home import Home

from thingsboard import ThingsboardConnection

def main():
    config = homematicip.find_and_load_config_file()
    home = Home()
    home.set_auth_token(config.auth_token)
    home.init(config.access_point)

    c = lambda: None
    c.__dict__ = config.raw_config['TB']
    tb = ThingsboardConnection(c)

    home.get_current_state()
    for g in home.groups:
        if g.groupType=="META":
            for d in g.devices:
                try:
                    x = tb.getOrCreateDevice(g, d)
                    x.updateTelemetryFromHmIP(g, d)
                except: #pylint: disable=bare-except
                    print(f"ERROR: updating telemetry from '{d.label}' {d.id}")


if __name__ == "__main__":
    main()
