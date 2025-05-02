from datetime import datetime, timedelta
import math
from appdaemon.plugins.hass.hassapi import Hass

"""
Add following sensor template to your configuration.yaml:
template:
  sensor:
    - name: "Sunshine Threshold"
      unique_id: sunshine_threshold
      unit_of_measurement: "lx"
      device_class: illuminance
      state_class: measurement
      icon: mdi:brightness-7
      state: >
        {{ states('sensor.sunshine_threshold') | float(default=0) }}
"""


class Sunshine(Hass):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Sunshine, cls).__new__(cls)
            # Set initialized flag
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, *args, **kwargs):
        # Only initialize once
        if not self._initialized:
            super().__init__(*args, **kwargs)
            self.azimuth = 0
            self.elevation = 0
            self.brightness = 0
            self.last_update = None
            self._initialized = True
            print("Initialized Sunshine singleton")
    
    def initialize(self):
        """Initialize the Sunshine app."""
        if not hasattr(self, 'app_initialized'):
            self.floor = int(self.args.get("floor", 10000))
            self.cap = int(self.args.get("cap", 70000))
            self.buffer = int(self.args.get("buffer", 10000))
            self.debug_mode = bool(self.args.get("debug", False))

            if self.args.get('entity'):
                if not self.entity_exists(self.args.get('entity')):
                    raise ValueError(f"Entity {self.args.get('entity')} doesn't exist in HASS. Please generate!")
            else:
                raise ValueError(f"Invalid configuration. Sunshine needs valid 'entity' to store results.")

            
            # Listen to sun changes and calculate new with every change
            self.listen_state(self.update_brightness, "sun.sun", attribute = "all")

            # First time start, manually triggering logic to not have to wait for first sun trigger
            sun_state = self.get_state("sun.sun", attribute="all")
            self.update_brightness(entity="manual_start", attribute={},old="",new=sun_state)

            self.app_initialized = True
            self.debug("AppDaemon initialization completed")

    def update_brightness(self, entity, attribute, old, new, *args, **kwargs):
        """Calculate and update brightness threshold."""
        try:
            # Get changed sun data from Home Assistant
            sunrise = datetime.fromisoformat(new['attributes']['next_rising'])
            self.debug(f"Sunrise: {sunrise}")
            sunset = datetime.fromisoformat(new['attributes']['next_setting'])
            self.debug(f"Sunrise: {sunset}")
            # Convert now to timezone-aware using the same timezone as sunrise
            now = datetime.now(sunrise.tzinfo)
            self.debug(f"Sunrise: {now}")

            if self.floor >= self.cap:
                self.log("IMPORTANT: Floor has to be lower than Cap", level="WARNING")
                self.cap = self.floor
                
            if self.buffer < 0:
                self.log("IMPORTANT: Buffer should be greater than 0", level="WARNING")
                self.buffer = 0
                
            # Calculate day brightness based on summer solstice
            day_brightness = self.get_day_brightness()

            # Ignore Date of sunrise and sunset, because we everytime get next event
            # So when last sunrise was reached today, the sunrise of tomorrow is supplied
            # The slight difference could be ignored
            if sunrise.time() <= now.time() <= sunset.time():

                # Calculate period between sunrise and sunset in minutes
                period = (datetime.combine(datetime.min, sunset.time()) - 
                    datetime.combine(datetime.min, sunrise.time())).total_seconds() / 60
                
                # Calculate minutes past since sunrise
                x = (datetime.combine(datetime.min, now.time()) - 
                    datetime.combine(datetime.min, sunrise.time())).total_seconds() / 60
                
                # Calculate sine curve parameters
                a = (day_brightness - self.buffer) / 2
                b = 2 * math.pi / period
                c = period / 4
                d = ((day_brightness - self.buffer) / 2) + self.buffer
                
                # Calculate result using sine function
                result = round(a * math.sin(b * (x - c)) + d)
            else:
                result = self.buffer
                
            # Create and update sensor through service call
            self.set_state(entity_id=self.args['entity'], state=float(result))
            self.debug(f"Updated Sunshine Brightness Threshold: {result}")
            
        except Exception as e:
            self.error(f"Error calculating brightness: {e}")

    def get_day_brightness(self):
        """Calculate brightness threshold based on distance to summer solstice."""
        if self.floor == self.cap:
            return self.cap
            
        next_solstice = self.get_next_solstice()
        diff_days = (next_solstice - datetime.now()).days
        
        brightness = self.floor + round(
            abs(diff_days - 183) * ((self.cap - self.floor) / 183)
        )
        
        if self.debug_mode:
            self.log(f"Day brightness threshold: {brightness}")
            
        return brightness

    def get_next_solstice(self):
        """Get next summer solstice date."""
        now = datetime.now()
        year = now.year
        
        # If we're past June 21st, use next year
        if now.month > 6 or (now.month == 6 and now.day > 21):
            year += 1
            
        return datetime(year, 6, 21)

    def debug(self, text):
        if self.args.get('DEBUG', False):
            self.log(text)