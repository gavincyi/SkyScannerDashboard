import os, sys
from flask import Flask, Blueprint, render_template, request
from datetime import datetime, timedelta
from query import FlightQuery, print_log

app = Flask(__name__)
webapp = Blueprint(__name__, __name__, static_folder='static')
config_file_path = sys.argv[1]
flight = FlightQuery(config_file_path)

@webapp.route('/', methods=['GET', 'POST'])
def index():
    results = {}
    if request.method == "POST":
        try:
            dept = request.form['dept-city']
            dest = request.form['dest-city']
            dept_date = request.form['dept-date']
            dest_date = request.form['dest-date']
            interval = (int)(request.form['interval'])
            dept = flight.top_autosuggest(dept)
            dest = flight.top_autosuggest(dest)
            start_date = datetime.strptime(dept_date, "%Y-%m-%d")
            end_date = datetime.strptime(dest_date, "%Y-%m-%d")
            date_diff = (end_date - start_date).days - interval + 1
            
            result = []
            for i in range(0, date_diff):
                from_date = start_date + timedelta(days=i)
                to_date = start_date + timedelta(days=i+date_diff)
                result += flight.Query(dept_place=dept,
                                      dest_place=dest,
                                      outbounddate=from_date.strftime("%Y-%m-%d"),
                                      inbounddate=to_date.strftime("%Y-%m-%d")).get_lowest_price()
            print_log("Webapp", "index", request.form)                                      
            print_log("Webapp", "index", date_diff)   
            print_log("Webapp", "index", result)                                      
            results = { 'result': result }
        except Exception as ex:
            print_log("Webapp", "index", request.form)
            print_log("Webapp", "index", ex)
    return render_template("index.html", **results)


def main():
    app.register_blueprint(webapp)
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
    
main()    