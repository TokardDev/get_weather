import requests
import click
import json
import datetime
from loguru import logger
import os


class Measurements:
    """A class to represent the measurements of a city.

    Args:
        town (str): The name of the city.
        country (str): The country code of the city.
    """

    def __init__(self, town, country):
        # store every date, for each date store all the measurements
        self._forecast = {}  # key : date, value : list of measurements
        self.forecast_location = f"{town}({country})"
        self.forecast_min_temp = 0
        self.forecast_max_temp = 0
        self.forecast_details = []  # store date, avg temp and measure count

    def add_temp(self, date, temp):
        """
        Add a temperature measurement to the forecast.
        Args:
            date (str): The date of the measurement.
            temp (float): The temperature of the measurement.
        """
        if date in self._forecast:  # if the date already exists
            self._forecast[date].append(temp)
        else:
            self._forecast[date] = [temp]

    @property
    def max_temp(self):
        """
        Get the maximum temperature of the forecast.
        Returns:
            float: The maximum temperature of the forecast.
        """
        # get the max temp for each day, and then the global max temp
        return max([max(temps) for temps in self._forecast.values()])

    @property
    def min_temp(self):
        """
        Get the minimum temperature of the forecast.
        Returns:
            float: The minimum temperature of the forecast.
        """
        # same as above but for min temp
        return min([min(temps) for temps in self._forecast.values()])

    def to_json(self):
        """
        Convert the forecast to a JSON string.
        Returns:
            str: The JSON string of the forecast.
        """
        self.forecast_min_temp = self.min_temp  # get the max and min
        self.forecast_max_temp = self.max_temp

        # skip the current day
        for date, temps in list(self._forecast.items())[1:]:

            # calculate the average temperature of the day
            avg = sum(temps)/len(temps)
            measure_count = len(temps)

            # round to 2 decimal places
            self.forecast_details.append({"date": date, "temp": round(avg, 2),
                                          "measure_count": measure_count})
        return json.dumps({
            "forecast_location": self.forecast_location,
            "forecast_min_temp": self.forecast_min_temp,
            "forecast_max_temp": self.forecast_max_temp,
            "forecast_details": self.forecast_details
        }, indent=4)


@click.command()
@click.argument('city', nargs=1)  # add cli params
@click.argument('country', nargs=1)
def get_weather(city, country):
    """
    Get the weather forecast of a city and save it to a JSON file.\n
    Args:\n
        city (str): The name of the city.\n
        country (str): The country code of the city.\n
    """  # I'm using \n to make the --help message more readable

    log_file = (
        f"logs/{city}({country})_"
        f"{datetime.date.today().strftime('%Y_%m_%d')}.log"
    )
    logger.add(log_file, rotation="1 MB", retention="7 days", level="INFO")

    # lis l'api key dans api_key.txt
    try:
        API_KEY = open("api_key.txt", "r").read()
        logger.success("Reading API key from api_key.txt")
    except FileNotFoundError:
        logger.error("api_key.txt not found")
        exit(1)
    BASE_URL = (
        f"http://api.openweathermap.org/data/2.5/forecast?appid={API_KEY}"
    )

    measure = Measurements(city, country)
    url = f"{BASE_URL}&q={city},{country}&units=metric"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:  # if correctly fetched
        logger.success(f"Data fetched successfully for {city}({country})")
        for mesurement in data["list"]:
            date = mesurement["dt_txt"].split(" ")[0]  # get the date
            temp = mesurement['main']['temp']
            measure.add_temp(date, temp)

        json_data = measure.to_json()  # convert class to json
        today = datetime.date.today()
        os.makedirs("out", exist_ok=True)
        json_name = f'out/{city}({country})_{today}.json'
        if os.path.exists(json_name):  # check if the file already exists
            logger.warning("File already exists, overwriting...")
        with open(json_name, 'w') as f:
            f.write(json_data)
        logger.success(f"Data saved successfully in /out/{json_name}")
    else:
        logger.error(f"Failed to fetch data for {city}({country})")
        # log the error message (city not found, wrong api key, etc)
        logger.error(data["message"])
        return


if __name__ == '__main__':
    print("""\033[94m
     ▄▄   ▄▄▄  ▄▄▄▄▄    ▄▄▌ ▐ ▄▌ ▄▄▄    ▄▄▄  ▄▄▄▄▄ ▄  ▄▄ ▄▄▄  ▄▄▄
    ▐█ ▀  ▀▄ ▀  ██      ██  █▌▐█ ▀▄ ▀  ▐█ ▀█   █   ██ ▐█ ▀▄ ▀ ▀▄ █
    ▄█ ▀█▄▐▀▀ ▄ ▐█      ██ ▐█▐▐▌ ▐▀▀ ▄ ▄█▀▀█   █   ██▀▀█ ▐▀▀ ▄▐▀▀▄ 
    ▐█▄ ▐█▐█▄▄▌ ▐█▌     ▐█▌██▐█▌ ▐█▄▄▌ ▐█  ▐▌  █▌  ██ ▐█ ▐█▄▄▌▐█ █▌
     ▀▀▀▀  ▀▀▀  ▀▀▀ ▄▄▄▄ ▀▀▀▀ ▀   ▀▀▀   ▀  ▀  ▀▀▀  ▀▀  ▀  ▀▀▀  ▀  ▀
    """)
    get_weather()
