import os, sys
from flask import Flask, Blueprint, render_template, request
from datetime import datetime, timedelta
from query import FlightQuery, print_log
from functools import partial

app = Flask(__name__)
webapp = Blueprint(__name__, __name__, static_folder='static')
config_file_path = sys.argv[1]
flight = FlightQuery(config_file_path)


def carrier_filtering(itinerary, welcome_carriers, unwelcome_carriers):
    """
    Filter the carriers.
    :param itinerary:
    :param welcome_carriers: List of welcoming carriers
    :param unwelcome_carriers: List of unwelcoming carriers
    :return: True if it passes the filtering
    """
    out_carriers = itinerary['OutboundLeg']['Carriers']
    in_carriers = itinerary['InboundLeg']['Carriers']

    if len(welcome_carriers) > 0:
        ret = False
        for carrier in welcome_carriers:
            ret |= any([c.find(carrier) > -1 for c in out_carriers]) or \
                any([c.find(carrier) > -1 for c in in_carriers])

        return ret
    elif len(unwelcome_carriers) > 0:
        ret = True
        for carrier in unwelcome_carriers:
            ret &= all([c.find(carrier) == -1 for c in out_carriers]) and \
                 all([c.find(carrier) == -1 for c in in_carriers])
        return ret
    else:
        return True


@webapp.route('/', methods=['GET', 'POST'])
def index():
    """
    Index page callback
    :return: Index page
    """
    results = {}
    if request.method == "POST":
        try:
            depts = [d.strip() for d in request.form['dept-city'].split(',')]
            dests = [d.strip() for d in request.form['dest-city'].split(',')]
            dept_date = request.form['dept-date']
            dest_date = request.form['dest-date']
            interval = int(request.form['interval'])
            carrier_filter = [c.strip() for c in request.form['carrier_filter'].split(',')]
            welcome_carriers = [c for c in carrier_filter if len(c) > 0 and c[0] != '-']
            unwelcome_carriers = [c[1:] for c in carrier_filter if len(c) > 0 and c[0] == '-']
            start_date = datetime.strptime(dept_date, "%Y-%m-%d")
            end_date = datetime.strptime(dest_date, "%Y-%m-%d")
            date_diff = (end_date - start_date).days - interval + 1
            result = []

            for dept in depts:
                for dest in dests:
                    # Loop through each destination and departure
                    dept = flight.top_autosuggest(dept)
                    dest = flight.top_autosuggest(dest)
                    for i in range(0, date_diff):
                        from_date = start_date + timedelta(days=i)
                        to_date = start_date + timedelta(days=i+interval)
                        temp_result = flight.Query(dept_place=dept,
                                              dest_place=dest,
                                              outbounddate=from_date.strftime("%Y-%m-%d"),
                                              inbounddate=to_date.strftime("%Y-%m-%d")
                                        )
                        result += temp_result.get_lowest_price(filter=partial(carrier_filtering,
                                                                              welcome_carriers=welcome_carriers,
                                                                              unwelcome_carriers=unwelcome_carriers))
            result.sort(key=lambda x: x['Price'])

            print_log("Webapp", "index", request.form)                                      
            print_log("Webapp", "index", date_diff)   
            print_log("Webapp", "index", result)                                      
            results = {'result': result, 'currency': flight.currency}
        except Exception as ex:
            print_log("Webapp", "index", request.form)
            print_log("Webapp", "index", ex)
    return render_template("index.html", **results)


def main():
    app.register_blueprint(webapp)
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
    
main()    