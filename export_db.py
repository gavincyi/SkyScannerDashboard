import sys
import sqlite3
from query import FlightQuery, print_log
from datetime import datetime, timedelta

class SqliteClient:
    def __init__(self, conf):
        self.conf = conf
        self.init()
    
    def init(self):
        self.conn = sqlite3.connect(self.conf.get_sqlite_file_path(), check_same_thread=False)
        

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python export_db.py <config_file>")
        sys.exit(0)
   
    config_file_path = sys.argv[1]
    flight = FlightQuery(config_file_path)
    db_client = SqliteClient(flight.conf)
    start_date = datetime.now() + timedelta(days=1)
    search_days = 1 ## flight.conf.get_search_days()
    departures = ['Hong Kong'] ## flight.conf.get_departure_cities()
    destinations = ['London'] ## flight.conf.get_destination_cities()
    departures_code = [flight.top_autosuggest(d) for d in departures]
    destinations_code = [flight.top_autosuggest(d) for d in destinations]
    travel_duration = flight.conf.get_travel_interval_days()
    
    for i in range(0, len(departures_code)):
        if departures_code[i] == "":
            print("Cannot find the city code of departure city %s" % departures[i])
    
    for i in range(0, len(destinations_code)):
        if destinations_code[i] == "":
            print("Cannot find the city code of destination city %s" % destinations[i])    
    
    for incr_day in range(0, search_days):
        for duration in range(travel_duration[0], travel_duration[1]+1):
            for departure in departures_code:
                for destination in destinations_code:
                    start = start_date + timedelta(days=incr_day)
                    end = start_date + timedelta(days=incr_day+duration)
                    result = flight.Query(dept_place=departure,
                                          dest_place=destination,
                                          outbounddate=start.strftime("%Y-%m-%d"),
                                          inbounddate=end.strftime("%Y-%m-%d"))
                    print(result.get_lowest_price())
    
    
