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
        print_log(self.__class__.__name__,
                  self.__init__.__name__,
                  "Configuration path = %s" % path)
        configparser.ConfigParser.__init__(self)
        self.read(path)
        print_log(self.__class__.__name__,
                  self.__init__.__name__,
                  "Configuration items:\n%s" % self.__dict__)

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


class FlightAgent:
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


class FlightCarrier:
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


class FlightPlace:
    """
    Place
    """
    def __init__(self, place_msg):
        """
        :param place_msg: Message of a place
        """
        self.Id = place_msg['Id']
        self.Type = place_msg['Type']
        self.Code = place_msg['Code']
        self.Name = place_msg['Name']


class FlightItineraryLeg:
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


class FlightItinerary:
    """
    Flight itinerary. 
    """
    class FlightPricingOption:
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
        return min([int(p.Price) for p in self.PricingOptions])

        
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
            self.Places = {}

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
                self.Legs[leg['Id']] = FlightItineraryLeg(leg)
            
            for agent in ret['Agents']:
                self.Agents[agent['Id']] = FlightAgent(agent)
            
            for carrier in ret['Carriers']:
                self.Carriers[carrier['Id']] = FlightCarrier(carrier)

            for place in ret['Places']:
                self.Places[place['Id']] = FlightPlace(place)

            for itinerary in ret['Itineraries']:
                self.Itineraries.append(FlightItinerary(itinerary))

        def get_itinerary_leg(self, leg_id):
            """
            :param leg_id - The itinerary leg ID            
            """            
            return self.Legs[leg_id]
        
        def get_lowest_price(self, n_itinerary=10, filter=None):
            """
            :param n_itinerary - The number of lowest price itineraries
            :return The first n-th lowest price itineraries
            """
            lowest = []
            for itinerary in self.Itineraries:
                i_dict = self.to_dict(itinerary)

                if filter is None or filter(i_dict):
                    lowest.append(i_dict)
                    if len(lowest) > n_itinerary:
                        lowest.sort(key=lambda x: x['Price'])
                        del lowest[-1]

            return lowest

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
            outbound['DestinationStation'] = self.Places[outbound['DestinationStation']].Name
            outbound['OriginStation'] = self.Places[outbound['OriginStation']].Name
            inbound['DestinationStation'] = self.Places[inbound['DestinationStation']].Name
            inbound['OriginStation'] = self.Places[inbound['OriginStation']].Name
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
                initial_delay=self.query_init_delay_sec, # Useless in current API
                delay=self.query_delay_sec # Useless in current API
                ).parsed
                   
        query_result = FlightQuery.FlightQueryResult(ret)    
            
        return query_result


class FlightCacheQuery(FlightsCache):
    class Types:
        CHEAPEST_QUOTES = 0,
        CHEAPEST_PRICE_BY_DATE = 1,
        GRID_PRICES_BY_DATE = 2

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

    def Query(self, dept_place, dest_place, outbounddate, inbounddate, type=Types.CHEAPEST_PRICE_BY_DATE):
        """
        Query all the flight prices based on human readable departure and
        destination places.
        :param dept_place - Departure location
        :param dest_place - Destination location
        :param outbounddate - Outbound date
        :param inbounddate - Inbound date
        :return All the itineraries
        """
        if type == FlightCacheQuery.Types.CHEAPEST_QUOTES:
            ret = self.get_cheapest_quotes(market=self.market,
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
        elif type == FlightCacheQuery.Types.GRID_PRICES_BY_DATE:
            ret = self.get_grid_prices_by_date(market=self.market,
                                               currency=self.currency,
                                               locale=self.locale,
                                               originplace=dept_place,
                                               destinationplace=dest_place,
                                               outbounddate=outbounddate,
                                               inbounddate=inbounddate)
        print(json.dumps(ret.parsed, indent=4))


def test_carrier_filter(itinerary):
    out_carriers = itinerary['OutboundLeg']['Carriers']
    in_carriers = itinerary['InboundLeg']['Carriers']

    return all([c.find('China') == -1 for c in out_carriers]) and \
        all([c.find('China') == -1 for c in in_carriers])


def test_flight_query():
    config_file_path = sys.argv[1]
    flight = FlightQuery(config_file_path)
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
        result = flight.Query(dept_place=dept,
                              dest_place=dest,
                              outbounddate=start.strftime("%Y-%m-%d"),
                              inbounddate=end.strftime("%Y-%m-%d"))
        lowest += result.get_lowest_price(filter=test_carrier_filter)

        if 1.0*i/total > prev_progress:
            print_log('[Default]',
                      'main',
                      "Progress {0:.0f}%".format(prev_progress))
            prev_progress += 0.1

    lowest.sort(key=lambda x: x['Price'])

    for l in lowest:
        print("================================")
        print(FlightQuery.FlightQueryResult.to_json(l))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python query.py <config file name>")
        sys.exit(1)
    test_flight_query()

