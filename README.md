# SkyScannerDashboard

The dashboard searches the cheapest flight ticket by the given conditions:

- Your possible start date

- Your possible end date

- Duration of the journal

- Range of departure and destination cities

- Carrier

The web server is developed under [flask](http://flask.pocoo.org/). 

### Prerequistie

The project is written in python. It is highly recommended to use pip install required libraries.

Use git to clone the whole project and install the required libraries.

```
git clone https://github.com/gavincyi/SkyScannerDashboard.git
cd SkyScannerDashboard
pip install -r requirement.txt
```

### Configuration

A few items should be set up in the configuration file default.ini before starting the server. Please register for a [skyscanner API](http://en.business.skyscanner.net/) before setting up the server.

|Item|Description|
|---|---|
|API_KEY|Skyscanner API key|
|MARKET|Country of the market, e.g. US, GB or HK|
|CURRENCY|Currency, e.g. USD, EUR, GBP, HKD|
|LOCALE|Language, e.g. en-US|
|ADULTS|Number of adults of each query|
|QUERY_INIT_DELAY_SEC|Initial delay of each API query in seconds|
|QUERY_DELAY_SEC|Delay of each API query in seconds|

### Start

1) Run the server

```
python run.py default.ini            # No SSL
python run.py default.ini --ssl      # SSL
```

Now the server is running under port 8080.

2) Place your query on the page.
![alt tag](/doc/sample.jpg)
