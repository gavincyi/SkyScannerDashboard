import os, sys, query
from flask import Flask, Blueprint, render_template
from datetime import datetime, timedelta

app = Flask(__name__)
webapp = Blueprint(__name__, __name__, static_folder='static')
config_file_path = sys.argv[1]
flight = query.FlightQuery(config_file_path)

@webapp.route('/')
def index():
    dept = flight.top_autosuggest('Hong Kong')
    dest = flight.top_autosuggest('Copenhagen')
    start_date = datetime(2017, 1, 1)
    interval = 7
    result = flight.Query(dept_place=dept,
                                  dest_place=dest,
                                  outbounddate=start_date.strftime("%Y-%m-%d"),
                                  inbounddate=(start_date + timedelta(days=interval)).strftime("%Y-%m-%d"))
    result = { 'result': result.get_lowest_price() }
    return render_template("index.html", **result)


def main():
    app.register_blueprint(webapp)
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
    
main()    