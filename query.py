import sys
from skyscanner.skyscanner import Flights, FlightsCache, EmptyResponse
from datetime import datetime, timedelta
import configparser
import json

def print_log(class_name, method_name, log_msg):
    print("%s - [%s::%s] - %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                  class_name,
                                  method_name, 
                                  log_msg))

class config(configparser.ConfigParser):
    """
    Configuration object. 
    """

    def __init__(self, path):
        """
        :param path - Configuration file path
        """
        configparser.ConfigParser.__init__(self)
        self.read(path)
    
    def get_api_key(self):
        """
        API key getter 
        """            
        return self['DEFAULT']['API_KEY']
    
    def get_market(self):
        """
        Market getter 
        """                        
        return self['DEFAULT']['MARKET']
        
    def get_currency(self):
        """
        Currency getter 
        """               
        return self['DEFAULT']['CURRENCY']
        
    def get_locale(self):
        """
        Locale getter 
        """                 
        return self['DEFAULT']['LOCALE']   
        
    def get_adults(self):
        """
        Adults getter 
        """                 
        return int(self['DEFAULT']['ADULTS'])
        
    def get_query_init_delay_sec(self):
        """
        Query initial delay time in seconds
        """                 
        return int(self['DEFAULT']['QUERY_INIT_DELAY_SEC'])       
        
    def get_query_delay_sec(self):
        """
        Query delay time in seconds
        """                 
        return int(self['DEFAULT']['QUERY_DELAY_SEC'])         

class FlightItinerary():
    """
    Flight itinerary. 
    """
    class FlightItineraryLeg():
        """
        Itinerary leg
        """
        def __init__(self, leg_msg):
            """
            :param leg_msg - Message of an itinerary leg
            """        
            self.Id = leg_msg['Id']
            self.OriginStation = leg_msg['OriginStation']
            self.DestinationStation = leg_msg['DestinationStation']
            self.Departure = leg_msg['Departure']
            self.Arrival = leg_msg['Arrival']
            self.Carriers = leg_msg['Carriers']
            self.Directionality = leg_msg['Directionality']                        
    
    class FlightPricingOption():
        """
        Pricing option
        """
        def __init__(self, price_msg):
            """
            :param price_msg - Message of a pricing option
            """
            self.Price = float(price_msg['Price'])
            self.Agents = price_msg['Agents']
            self.QuoteAgeInMinutes = price_msg['QuoteAgeInMinutes']

    class FlightAgent():
        """
        Agent
        """
        def __init__(self, agent_msg):
            """
            :param agent_msg - Message of an agent
            """
            self.Id = agent_msg['Id']
            self.Name = agent_msg['Name']
            self.OptimisedForMobile = agent_msg['OptimisedForMobile']
            self.Type = agent_msg['Type'] 
    
    class FlightCarrier():
        """
        Carrier
        """
        def __init__(self, carrier_msg):
            """
            :param carrier_msg - Message of a carrier
            """
            self.Id = carrier_msg['Id']
            self.DisplayCode = carrier_msg['DisplayCode']
            self.Code = carrier_msg['Code']
            self.Name = carrier_msg['Name']
            
    def __init__(self, msg):
        """
        :param msg - Message of an itinerary
        """
        self.OutboundLegId = msg['OutboundLegId']
        self.InboundLegId = msg['InboundLegId']
        self.PricingOptions = [FlightItinerary.FlightPricingOption(p) for p in msg['PricingOptions']]
                 
    def get_lowest_price(self):
        """
        :return The lowest price among the pricing option
        """
        return min([p.Price for p in self.PricingOptions])

        
class FlightQuery(Flights):
    class FlightQueryResult:
        """
        Flight query result
        """
        def __init__(self, ret):
            """
            :param ret - Parsed query result
            """
            self.Itineraries = []
            self.Legs = {}
            self.Agents = {}
            self.Carriers = {} 

            try:
                query = ret['Query']
                self.InboundDate = query['InboundDate']
                self.DestinationPlace = query['DestinationPlace']
                self.CabinClass = query['CabinClass']
                self.Adults = query['Adults']
                self.Locale = query['Locale']
                self.Country = query['Country']
                self.OutboundDate = query['OutboundDate']
                self.Currency = query['Currency']
                self.OriginPlace = query['OriginPlace']
                self.GroupPricing = query['GroupPricing']
            except TypeError as nt:
                print_log(self.__class__.__name__, 
                          self.__init__.__name__,
                          "%s\n%s" % (nt, ret))
                raise nt
            
            for leg in ret['Legs']:
                self.Legs[leg['Id']] = FlightItinerary.FlightItineraryLeg(leg)
            
            for agent in ret['Agents']:
                self.Agents[agent['Id']] = FlightItinerary.FlightAgent(agent)
            
            for carrier in ret['Carriers']:
                self.Carriers[carrier['Id']] = FlightItinerary.FlightCarrier(carrier)
            
            for itinerary in ret['Itineraries']:
                self.Itineraries.append(FlightItinerary(itinerary))   
        
        def get_itinerary_leg(self, leg_id):
            """
            :param leg_id - The itinerary leg ID            
            """            
            return self.Legs[leg_id]
        
        def get_lowest_price(self, n_itinerary=1, n_agent=1):
            """
            :param n_itinerary - The number of lowest price itineraries
            :param n_agent - The number of agents
            :return The first n-th lowest price itineraries
            """
            lowest = []
            for itinerary in self.Itineraries:
                lowest.append(itinerary)
                if len(lowest) > n_itinerary:
                    lowest.sort(key=lambda x: x.get_lowest_price())
                    del lowest[-1]

            for l in lowest:
                l.PricingOptions = l.PricingOptions[0:n_agent]

            return [self.to_dict(l) for l in lowest]

        def to_dict(self, itinerary):
            """
            :param itinerary: Flight itinerary
            :return Converted to a readable dictionary
            """
            ret = dict()
            outbound = dict(self.Legs[itinerary.OutboundLegId].__dict__)
            inbound = dict(self.Legs[itinerary.InboundLegId].__dict__)
            outbound['Carriers'] = [self.Carriers[e].Name for e in outbound['Carriers']]
            inbound['Carriers'] = [self.Carriers[e].Name for e in inbound['Carriers']]
            ret['OutboundLeg'] = outbound
            ret['InboundLeg'] = inbound
            ret['Price'] = itinerary.get_lowest_price()

            return ret

        @staticmethod
        def to_json(itinerary):
            """
            :param itinerary: Readable itinerary
            :return: The itinerary in json format
            """
            return json.dumps(itinerary, default=lambda o: o.__dict__, indent=4)

    def __init__(self, config_path):
        """
        :param config_path - Configuration file path
        """
        self.conf = config(config_path)
        self.market = self.conf.get_market()
        self.currency = self.conf.get_currency()
        self.locale = self.conf.get_locale()
        self.adults = self.conf.get_adults()
        self.query_init_delay_sec = self.conf.get_query_init_delay_sec()
        self.query_delay_sec = self.conf.get_query_delay_sec()
        Flights.__init__(self, self.conf.get_api_key())
        
    def top_autosuggest(self, keyword):
        """
        Get the top auto suggestion on location
        :param keyword - Keyword to search for location auto suggestion
        """        
        ret = self.location_autosuggest(query=keyword,
                                      market=self.market,
                                      currency=self.currency,
                                      locale=self.locale).parsed

        return ret['Places'][0]['PlaceId']

    def Query(self, dept_place, dest_place, outbounddate, inbounddate):
        """
        Query all the flight prices based on human readable departure and
        destination places.
        :param dept_place - Departure location
        :param dest_place - Destination location
        :param outbounddate - Outbound date
        :param inbounddate - Inbound date
        :return All the itineraries
        """
        ret = self.get_result(
                country=self.market,
                currency=self.currency,
                locale=self.locale,
                originplace=dept_place,
                destinationplace=dest_place,
                outbounddate=outbounddate,
                inbounddate=inbounddate,
                adults=self.adults,
                initial_delay=self.query_init_delay_sec,
                delay=self.query_delay_sec).parsed
                   
        query_result = FlightQuery.FlightQueryResult(ret)    
            
        return query_result


class FlightCacheQuery(FlightsCache):
    class Types:
        CHEAPEST_QUOTES = 0,
        CHEAPEST_PRICE_BY_ROUTE = 1,
        CHEAPEST_PRICE_BY_DATE = 2,
        GRID_PRICES_BY_DATE = 3

    def __init__(self, config_path):
        """
        Constructor
        :param config_path: Configuration file path
        """
        self.conf = config(config_path)
        self.market = self.conf.get_market()
        self.currency = self.conf.get_currency()
        self.locale = self.conf.get_locale()
        self.query_init_delay_sec = self.conf.get_query_init_delay_sec()
        self.query_delay_sec = self.conf.get_query_delay_sec()
        FlightsCache.__init__(self, self.conf.get_api_key())

    def top_autosuggest(self, keyword):
        """
        Get the top auto suggestion on location
        :param keyword - Keyword to search for location auto suggestion
        """
        ret = self.location_autosuggest(query=keyword,
                                        market=self.market,
                                        currency=self.currency,
                                        locale=self.locale).parsed

    def Query(self, dept_place, dest_place, outbounddate, inbounddate, type=Types.CHEAPEST_QUOTES):
        """
        Query all the flight prices based on human readable departure and
        destination places.
        :param dept_place - Departure location
        :param dest_place - Destination location
        :param outbounddate - Outbound date
        :param inbounddate - Inbound date
        :return All the itineraries
        """
        if type == FlightCacheQuery.Types.GRID_PRICES_BY_DATE:
            ret = self.get_grid_prices_by_date(market=self.market,
                                               currency=self.currency,
                                               locale=self.locale,
                                               originplace=dept_place,
                                               destinationplace=dest_place,
                                               outbounddate=outbounddate,
                                               inbounddate=inbounddate)
        elif type == FlightCacheQuery.Types.CHEAPEST_PRICE_BY_DATE:
            ret = self.get_cheapest_price_by_date(market=self.market,
                                                  currency=self.currency,
                                                  locale=self.locale,
                                                  originplace=dept_place,
                                                  destinationplace=dest_place,
                                                  outbounddate=outbounddate,
                                                  inbounddate=inbounddate)
        elif type == FlightCacheQuery.Types.CHEAPEST_QUOTES:
            ret = self.get_cheapest_quotes(market=self.market,
                                           currency=self.currency,
                                           locale=self.locale,
                                           originplace=dept_place,
                                           destinationplace=dest_place,
                                           outbounddate=outbounddate,
                                           inbounddate=inbounddate)
        print(json.dumps(ret.parsed, indent=4))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python query.py <config file name>")
        sys.exit(1)

    config_file_path = sys.argv[1]
    flight = FlightQuery(config_file_path)
    flightCache = FlightCacheQuery(config_file_path)
    start_date = datetime(2017, 1, 1)
    interval = 7
    lowest = []
    dept = flight.top_autosuggest('Hong Kong')
    dest = flight.top_autosuggest('Copenhagen')
    total = 1
    prev_progress = 0.0
    for i in range(0, total):
        start = start_date + timedelta(days=i)
        end = start_date + timedelta(days=i+interval)
        result = flightCache.Query(dept_place=dept,
                              dest_place=dest,
                              outbounddate='2017-01',
                              inbounddate='2017-02')
                              # outbounddate=start.strftime("%Y-%m-%d"),
                              # inbounddate=end.strftime("%Y-%m-%d"))
        # lowest += result.get_lowest_price()
        
        if 1.0*i/total > prev_progress:
            print_log('[Default]',
                      'main',
                      "Progress {0:.0f}%".format(prev_progress))
            prev_progress += 0.1

    # lowest.sort(key=lambda x: x['Price'])
    #
    # for l in lowest:
    #     print("================================")
    #  print(FlightQuery.FlightQueryResult.to_json(l))
