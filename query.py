from skyscanner.skyscanner import Flights
import configparser
import json


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
        self.InboundLegId = msg['OutboundLegId']
        self.PricingOptions = [FlightItinerary.FlightPricingOption(p) for p in msg['PricingOptions']]
                 
    def get_lowest_price(self):
        return min([p.Price for p in self.PricingOptions])
        
class FlightQuery(Flights):
    class FlightQueryResult():
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
        
        def get_lowest_price(self, number):
            """
            :param number - The number of lowest price itineraries
            :return The first n-th lowest price itineraries
            """
            lowest = []
            for itinerary in self.Itineraries:
                lowest.append(itinerary)
                if len(lowest) > number:
                    lowest.sort(key=lambda x: x.get_lowest_price())
                    del lowest[-1]
            
            return lowest                    

    def __init__(self, config_path):
        """
        :param config_path - Configuration file path
        """
        self.conf = config(config_path)
        self.market = self.conf.get_market()
        self.currency = self.conf.get_currency()
        self.locale = self.conf.get_locale()
        self.adults = self.conf.get_adults()
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
        itineraries = []
        legs = {}
        agents = {}
        carriers = {}
        dept = self.top_autosuggest(dept_place)
        dest = self.top_autosuggest(dest_place)
        ret = self.get_result(
                country=self.market,
                currency=self.currency,
                locale=self.locale,
                originplace=dept,
                destinationplace=dest,
                outbounddate=outbounddate,
                inbounddate=inbounddate,
                adults=self.adults).parsed
                       
        query_result = FlightQuery.FlightQueryResult(ret)                       
        return query_result
                                                  

if __name__ == '__main__':
    flight = FlightQuery('config.ini')
    
    result = flight.Query(dept_place='Hong Kong', 
                          dest_place='Copenhagen',
                          outbounddate='2017-01-20',
                          inbounddate='2017-01-25')

    lowest = result.get_lowest_price(3)
    
    for l in lowest:
        print("================================")
        print("OutboundLegId = %s" % l.OutboundLegId)
        print("InboundLegId = %s" % l.InboundLegId)
        print("Price = %.2f" % l.get_lowest_price())