from http.client import REQUEST_TIMEOUT
from colorama import Cursor
from flask import Flask, render_template, session, request, redirect, url_for
import pymysql
import hashlib
import json
from datetime import datetime, timedelta
import jinja2

# Configure Flask
app = Flask(__name__)

app.config['SECRET_KEY'] = "abcde"
app.config['APP_HOST'] = "localhost"

app.config['DB_USER'] = 'root'
app.config['DB_PASSWORD'] = ""
app.config['APP_DB'] = "project"
app.config['CHARSET'] = 'utf8mb4'

# Configure MySQL
conn = pymysql.connect(
    host = app.config['APP_HOST'],
    user = app.config['DB_USER'],
    password = app.config['DB_PASSWORD'],
    db = app.config['APP_DB'],
    charset = app.config['CHARSET'],
    cursorclass = pymysql.cursors.DictCursor
)

@app.route('/')
def index():
    if (session):
        return redirect(url_for('customerHomePage'))
    cursor = conn.cursor()
    query = 'SELECT username FROM airline_staff WHERE first_name="Leo"'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('index.html', staff = data)


#=========================== Customer's Functions ============================
@app.route('/customerHomePage')
def customerHomePage():
    return render_template('customerHomePage.html')

@app.route('/loginCustomerAuth', methods = ['GET', 'POST'])
def loginAuthCustomer():
    cursor = conn.cursor()
    email = request.form['email']
    password = request.form['password']
    password = hashlib.md5(password.encode())
    try:
        query = 'SELECT * FROM customer WHERE email = %s'
        
        cursor.execute(query, (email))

        data = cursor.fetchone()

        cursor.close()
        error = None

        print(password.hexdigest()[:20])
        print(data['password'])

        if(password.hexdigest()[:20] == data['password']):
            session['email'] = email
            session['name'] = data['name']
        return redirect(url_for('customerHomePage'))
    except:
        #returns an error message to the html page
        
        error = 'Invalid login or username'
        return render_template('index.html', error=error)

@app.route('/registerCustomerAuth', methods = ['GET', 'POST'])
def registerAuthCustomer():
    name = request.form['name']
    email  = request.form['email']
    password = request.form['password']
    building = request.form['building']
    city = request.form['city']
    street = request.form['street']
    state = request.form['state']
    phone = request.form['phone']
    passportnum = request.form['passport']
    passportcountry = request.form['passport_country']
    passportexp = request.form['passportexpiry']
    dateofbirth = request.form['dateofbirth']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Customer WHERE email = %s'
    cursor.execute(query, (email))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "Sorry! This user already exists."
        return render_template('index.html', error = error)
    else:
        ins = 'INSERT INTO customer(email, name, password, building_number, street, city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        #hash passwords before inserting into databse 
        password = hashlib.md5(password.encode()).hexdigest()[:20]
        cursor.execute(ins, (email, name, password, building, street, city, state, phone, passportnum, passportexp, passportcountry, dateofbirth ))
        conn.commit()
        cursor.close()
        return render_template('index.html', message = "Registered Successfully. Now please log in. ")


#============================ Staff's Functions =============================

@app.route('/staffHomePage', methods = ['GET', 'POST'])
def staffHomePage():
    if session['login'] and session['role'] == 'staff':
        username = session['username']
        airline = session['airline']
        flights = staff_view_flights(airline)
        number = getStaffPhone(username)
        print('flights',flights)
        return render_template("staffHomePage.html", username = username, flights = flights, number = number)
    else:
        return render_template("error.html", error = 'Staff is not logged in')

@app.route('/loginStaffAuth', methods = ['GET', 'POST'])
def loginStaffAuth():
    cursor = conn.cursor()
    username = request.form['username']
    password = request.form['password']
    password = hashlib.md5(password.encode())
    try:
        query = 'SELECT * FROM airline_staff WHERE username = %s'
        
        cursor.execute(query, (username))

        data = cursor.fetchone()

        cursor.close()
        error = None

        print(password.hexdigest())
        print(data['password'])

        if(password.hexdigest() == data['password']):
            session['username'] = username
            session['role'] = 'staff'
            session['airline'] = data['airline_name']
            session['login'] = True
        return redirect(url_for('staffHomePage'))
    except:
        #returns an error message to the html page
        
        error = 'Invalid login or username'
        return render_template('index.html', error=error)

@app.route('/registerStaffAuth', methods = ['POST'])
def registerStaffAuth():
    username = request.form['username']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    password = request.form['password']
    dateofbirth = request.form['dateofbirth']
    airlinename = request.form['airlinename']

    error_airline = None 
    error_username = None 

    cursor_airlinecheck = conn.cursor()
    cursor_usernamecheck = conn.cursor()
    query_airlinecheck = 'SELECT * from airline WHERE name = %s'
    query_usernamecheck = 'SELECT * FROM airline_staff WHERE username = %s'
    
    cursor_airlinecheck.execute(query_airlinecheck, (airlinename))
    cursor_usernamecheck.execute(query_usernamecheck, (username))

    data_airlinecheck = cursor_airlinecheck.fetchall()
    data_usernamecheck = cursor_usernamecheck.fetchall()

    
    if not data_airlinecheck:
        error_airline = "Sorry! This airline isn't currently registered with our system." 

    if data_usernamecheck:
        error_username = "Sorry! This username is already taken."

    if error_airline or error_username:
        if error_username:
            return render_template('index.html', error = error_username)
        return render_template('index.html', error = error_airline)

    cursor = conn.cursor()
    query_signup = 'INSERT INTO airline_staff(username, airline_name, password, first_name, last_name, date_of_birth) VALUES(%s, %s, %s, %s, %s, %s)'
    password = hashlib.md5(password.encode()).hexdigest()
    cursor.execute(query_signup, (username, airlinename, password, firstname, lastname, dateofbirth))
    conn.commit()
    cursor.close()
    
    return render_template('index.html', message = 'Signed up successfully. Now please login.')

# add phone
@app.route('/add_phone')
def add_phone():
    if session['login'] and session['role'] == 'staff':
        username = session['username']
        data = getStaffPhone(username)
        return render_template('add_phone.html', number = data)
    else:
        return render_template("error.html", error = "add phone fail")

@app.route('/post_phone', methods=['GET', 'POST'])
def post_phone():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        username = session['username']
        phone_number = request.form['phone_number']
        query = 'INSERT INTO staff_phone(username, phone_number) VALUES (%s, %s)'
        cursor.execute(query, (username, phone_number))
        conn.commit()
        cursor.close()
        return redirect(url_for('add_phone'))
    else:
        return render_template("error.html", error = "post phone fail")

# view flight use cases
@app.route("/view_flight_staff",methods=['GET', 'POST'])
def view_flight_staff():
    if session['login'] and session['role'] == 'staff':
        #username = session.get('username')
        airline = session['airline']
        data = staff_view_flights_30_days(airline)
        print(data)
        return render_template("view_flight_staff.html", show = True, flights = data,error=None)
    else:
        return render_template("error.html", error = "User not logged in")

@app.route("/view_flight_date",methods=['GET', 'POST'])
def view_flight_date():
    if session['login'] and session['role'] == 'staff':
        if request.method == 'POST':
            cursor = conn.cursor()
            start = request.form['start time']
            datetime.strptime(start, '%Y-%m-%dT%H:%M')
            end = request.form['end time']
            datetime.strptime(end, '%Y-%m-%dT%H:%M')
            airline = session['airline']
            query = 'SELECT * FROM flight WHERE flight.airline_name = %s  AND (flight.departure_datetime BETWEEN %s AND %s)'
            cursor.execute(query, (airline,start, end))
            data = cursor.fetchall()
            if data:
                return render_template("view_flight_date.html", show = True, flights = data, error=None)
            else:
                return render_template("view_flight_date.html", show = False, flights = None, error='Flight cannot be found')
        else:
            return render_template("view_flight_date.html", show = False, flights = None,error=None)
    else:
        return render_template("error.html", error = "User not logged in")

@app.route("/view_flight_departure",methods=['GET', 'POST'])
def view_flight_departure():
    if session['login'] and session['role'] == 'staff':
        if request.method == 'POST':
            cursor = conn.cursor()
            departure_airport = request.form['departure']
            airline = session['airline']
            query = 'SELECT * FROM flight WHERE flight.airline_name = %s  AND flight.departure_airport_code = %s'
            cursor.execute(query, (airline,departure_airport))
            data = cursor.fetchall()
            if data:
                return render_template("view_flight_departure.html", show = True, flights = data, error=None)
            else:
                return render_template("view_flight_departure.html", show = False, flights = None, error='Flight cannot be found')
        else:
            return render_template("view_flight_departure.html", show = False, flights = None,error=None)
    else:
        return render_template("error.html", error = "User not logged in")

@app.route("/view_flight_arrival",methods=['GET', 'POST'])
def view_flight_arrival():
    if session['login'] and session['role'] == 'staff':
        if request.method == 'POST':
            cursor = conn.cursor()
            arrival_airport = request.form['arrival']
            airline = session['airline']
            query = 'SELECT * FROM flight WHERE flight.airline_name = %s  AND flight.arrival_airport_code = %s'
            cursor.execute(query, (airline,arrival_airport))
            data = cursor.fetchall()
            if data:
                return render_template("view_flight_arrival.html", show = True, flights = data, error=None)
            else:
                return render_template("view_flight_arrival.html", show = False, flights = None, error='Flight cannot be found')
        else:
            return render_template("view_flight_arrival.html", show = False, flights = None,error=None)
    else:
        return render_template("error.html", error = "User not logged in")

@app.route('/create_new_flights')
def create_new_flights():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        #username = session['username']
        airline = session['airline']
        query = 'SELECT flight.airplane_ID, flight.airline_name, flight.flight_num, flight.base_price, flight.status, flight.departure_datetime, flight.arrival_datetime, flight.departure_airport_code, flight.arrival_airport_code FROM flight WHERE flight.airline_name = %s'
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        cursor.close()
        return render_template('create_new_flights.html', data = data)
    else:
        return render_template("error.html", error = "User not logged in")


@app.route('/post_new_flights',methods=['GET', 'POST'])
def post_new_flights():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        flight_num = request.form['flight_num']
        airplane_ID = request.form['airplane_ID']
        airline_name = request.form['airline_name']
        base_price = request.form['base_price']
        status = request.form['status']
        departure_datetime = request.form['departure_datetime']
        departure_airport_code = request.form['departure_airport_code']
        arrival_datetime = request.form['arrival_datetime']
        arrival_airport_code = request.form['arrival_airport_code']

        query = 'INSERT INTO flight(flight_num, airplane_ID, airline_name, base_price, status, departure_datetime, departure_airport_code, arrival_datetime, arrival_airport_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (flight_num, airplane_ID, airline_name,  base_price, status, departure_datetime, departure_airport_code,arrival_datetime, arrival_airport_code))
        conn.commit()
        cursor.close()
        return redirect(url_for("create_new_flights"))
    else:
        return render_template("error.html", error="User not logged in")
        
@app.route('/add_airport')
def add_airport():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        query = 'SELECT code, name, city, country, airport_type FROM airport'
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return render_template('add_airport.html', data = data)
    else:
        return render_template("error.html", error = "add airport fail")

@app.route('/post_airport', methods=['GET', 'POST'])
def post_airport():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        code = request.form['code']
        name = request.form['name']
        city = request.form['city']
        country = request.form['country']
        airport_type = request.form['airport_type']
        query = 'INSERT INTO airport(code, name, city, country, airport_type) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(query, (code, name, city, country, airport_type))
        conn.commit()
        cursor.close()
        return redirect(url_for('add_airport'))
    else:
        return render_template("error.html", error = "post airport fail")

@app.route('/add_airplane')
def add_airplane():
    if session['login'] and session['role'] == 'staff':
        #username = session['username']
        airline = session['airline']
        cursor = conn.cursor()
        query = 'SELECT airplane.ID, airplane.airline_name, airplane.num_seats, airplane.manufacturer, airplane.age FROM airplane WHERE airplane.airline_name = %s'
        cursor.execute(query,(airline))
        data = cursor.fetchall()
        cursor.close()
        return render_template('add_airplane.html', data = data)
    else:
        return render_template("error.html", error = "add airplane fail")

@app.route('/post_airplane', methods=['GET', 'POST'])
def post_airplane():
    if session['login'] and session['role'] == 'staff':
        #username = session['username']
        airline_name = session['airline']
        cursor = conn.cursor()
        ID = request.form['ID']
        num_seats = request.form['num_seats']
        manufacturer = request.form['manufacturer']
        age = request.form['age']
        query = 'INSERT INTO airplane(ID, airline_name, num_seats, manufacturer, age) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(query, (ID, airline_name, num_seats, manufacturer, age))
        conn.commit()
        cursor.close()
        return redirect(url_for('add_airplane'))
    else:
        return render_template("error.html", error = "post airplane fail")

@app.route('/change_status', methods = ['GET', 'POST'])
def change_status():
    if request.method == 'POST':
        if session['login'] and session['role'] == 'staff':
            cursor = conn.cursor()
            #username = session['username']
            airline = session['airline']
            flight_num = request.form['flight_num']
            departure_datetime = request.form['departure_datetime']
            status = request.form['status']
            datetime.strptime(departure_datetime, '%Y-%m-%dT%H:%M')
            query = 'SELECT * FROM flight WHERE flight.flight_num = %s AND flight.departure_datetime = %s AND flight.airline_name = %s'
            cursor.execute(query,(flight_num, departure_datetime, airline))
            data = cursor.fetchone()
            if data:
                update_query = 'UPDATE flight SET status = %s WHERE flight_num = %s AND departure_datetime = %s'
                cursor.execute(update_query, (status, flight_num, departure_datetime))
                conn.commit()
                cursor.close()
                return redirect(url_for('staffHomePage'))
            else:
                cursor.close()
                error = 'Cannot find flight'
                return render_template('change_status_of_flights.html', error = error)
        else:
            return render_template("error.html", error="Session fail")
    else:
        return render_template('change_status_of_flights.html', error = None)

@app.route('/view_flight_ratings', methods = ['GET', 'POST'])
def view_flight_ratings():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        #username = session['username']
        airline = session['airline']
        query = 'SELECT rate.flight_num, rate.email, rate.rating, rate.comment FROM flight, rate WHERE flight.airline_name = %s AND flight.flight_num = rate.flight_num ORDER BY rate.flight_num'
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        cursor.close()
        return render_template('view_flight_ratings.html', data = data)
    else:
        return render_template("error.html", error = "View flight rating fail")

@app.route('/view_frequent_customers', methods = ['GET', 'POST'])
def view_frequent_customers():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        #username = session['username']
        airline = session['airline']
        query = 'SELECT customer.name, customer.email FROM ticket, customer WHERE ticket.airline_name = %s AND ticket.email = customer.email AND ticket.departure_datetime BETWEEN DATE_ADD(CURDATE(), INTERVAL -1 year) AND CURDATE() GROUP BY customer.email ORDER BY (count(customer.name)) DESC'
        cursor.execute(query, (airline))
        data = cursor.fetchall()
        cursor.close()
        return render_template('view_frequent_customers.html', data=data)
    else:
        return render_template("error.html", error="View frequent customer fail")

@app.route('/view_frequent_customers_flight', methods = ['GET', 'POST'])
def view_frequent_customers_flight():
    if session['login'] and session['role'] == 'staff':
        if request.method == 'POST':
            cursor = conn.cursor()
            email = request.form['email']
            airline = session['airline']
            query = 'SELECT flight.airplane_ID, flight.airline_name, flight.flight_num, flight.base_price, flight.status, flight.departure_datetime, flight.arrival_datetime, flight.departure_airport_code, flight.arrival_airport_code FROM flight, ticket WHERE flight.airline_name = %s AND flight.airline_name = ticket.airline_name  AND flight.flight_num = ticket.flight_num AND flight.departure_datetime = ticket.departure_datetime AND ticket.email = %s'
            cursor.execute(query, (airline,email))
            data = cursor.fetchall()
            if data:
                return render_template("view_frequent_customers_flight.html", show = True, flights = data, error=None)
            else:
                return render_template("view_frequent_customers_flight.html", show = False, flights = None, error='Flight cannot be found')
        else:
            return render_template("view_frequent_customers_flight.html", show = False, flights = None,error=None)
    else:
        return render_template("error.html", error = "User not logged in")

@app.route('/view_report', methods = ['GET', 'POST'])
def view_report():
    if request.method == 'POST':
        if session['login'] and session['role'] == 'staff':
            cursor = conn.cursor()
            airline = session['airline']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            
            query = "SELECT MONTHNAME(purchase_datetime) as month, YEAR(purchase_datetime) AS year, COUNT(ID_num) as ticket_number FROM ticket WHERE airline_name = %s AND purchase_datetime BETWEEN %s and %s GROUP BY YEAR(purchase_datetime), MONTH(purchase_datetime)"
            cursor.execute(query, (airline, start_date, end_date))
            data = cursor.fetchall()
            print(data)
            if data:
                return render_template('view_report.html', error = None, data = data, months = len(data))
            else:
                error = 'No report found'
                return render_template('view_report.html', error = error, data = None, months = 0)
        else:
            return render_template("error.html", error="Session fail")
    else:
        return render_template('view_report.html', error = None, data = None, months = 0)

@app.route('/view_earned_revenue', methods = ['GET', 'POST'])
def view_earned_revenue():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        #username = session['username']
        airline = session['airline']
        query_year = 'SELECT sum(ticket.sold_price) FROM ticket WHERE ticket.airline_name = %s AND ticket.purchase_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE() GROUP BY ticket.airline_name'
        query_month = 'SELECT sum(ticket.sold_price) FROM ticket WHERE ticket.airline_name = %s AND ticket.purchase_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 month) AND CURDATE() GROUP BY ticket.airline_name'
        cursor.execute(query_year, (airline))
        lastyear = cursor.fetchone()
        cursor.execute(query_month, (airline))
        lastmonth = cursor.fetchone()
        cursor.close()
        return render_template('view_earned_revenue.html', lastyear = lastyear, lastmonth = lastmonth)
    else:
        return render_template("error.html", error="Session fail")

@app.route('/view_earned_revenue_by_class', methods = ['GET', 'POST'])
def view_earned_revenue_by_class():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        #username = session['username']
        airline = session['airline']
        query_first = "SELECT sum(ticket.sold_price) FROM ticket WHERE ticket.airline_name = %s AND ticket.travel_class = 'first' GROUP BY ticket.airline_name"
        query_business = "SELECT sum(ticket.sold_price) FROM ticket WHERE ticket.airline_name = %s AND ticket.travel_class = 'business' GROUP BY ticket.airline_name"
        query_economy = "SELECT sum(ticket.sold_price) FROM ticket WHERE ticket.airline_name = %s AND ticket.travel_class = 'economy' GROUP BY ticket.airline_name"
        cursor.execute(query_first, (airline))
        first = cursor.fetchone()
        cursor.execute(query_business, (airline))
        business = cursor.fetchone()
        cursor.execute(query_economy, (airline))
        economy = cursor.fetchone()
        cursor.close()
        return render_template('view_earned_revenue_by_class.html', first = first, business = business, economy = economy)
    else:
        return render_template("error.html", error="Session fail")

@app.route('/view_top_destinations', methods = ['GET', 'POST'])
def view_top_destinations():
    if session['login'] and session['role'] == 'staff':
        cursor = conn.cursor()
        #username = session['username']
        airline = session['airline']
        query_year = 'SELECT airport.city FROM ticket, flight, airport WHERE ticket.airline_name = %s AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE()) GROUP BY airport.city ORDER BY (count(airport.city)) DESC LIMIT 3'
        query_month = 'SELECT airport.city FROM ticket, flight, airport WHERE ticket.airline_name = %s AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -3 month) AND CURDATE()) GROUP BY airport.city ORDER BY (count(airport.city)) DESC LIMIT 3'
        cursor.execute(query_year, (airline))
        lastyear = cursor.fetchone()
        cursor.execute(query_month, (airline))
        last3months = cursor.fetchone()
        cursor.close()
        print(lastyear)
        print(last3months)
        return render_template('view_top_destinations.html', lastyear = lastyear, last3months = last3months)
    else:
        return render_template("error.html", error="Session fail")

#================================ Other Functions =================================

@app.route('/searchFlights', methods = ['GET', 'POST'])
def searchFlights():
    cursor = conn.cursor()
    print(request)
    departure_city = request.form['departure_city']
    arrival_city = request.form['arrival_city']
    departure_date = request.form['departure_date']
    #type_of_trip = request.form('')
    departure_midnight = datetime.strptime(departure_date, '%Y-%m-%d') + timedelta(days = 1)
    
    query = 'SELECT airport.code FROM airport WHERE airport.city = %s'

    cursor.execute(query,(departure_city))
    departure_airport_ids = cursor.fetchall()
    departure_airport_ids = tuple([id['code'] for id in departure_airport_ids])

    print(departure_date)
    print(departure_midnight)

    query = 'SELECT airport.code FROM airport WHERE airport.city = %s'
    cursor.execute(query, (arrival_city))
    arrival_airport_ids = cursor.fetchall()
    arrival_airport_ids = tuple([id['code'] for id in arrival_airport_ids])


    query = '''
        SELECT flight.flight_num, flight.arrival_airport_code, flight.departure_airport_code, flight.airline_name, flight.departure_datetime, flight.arrival_datetime, flight.status, flight.base_price, airplane.num_seats, COUNT(Ticket.ID_num ) as Ticket_Count  
        FROM flight  
        inner join airplane on flight.airplane_ID = airplane.ID left outer join ticket on flight.flight_num = ticket.flight_num
        WHERE flight.departure_airport_code in %s and flight.arrival_airport_code in %s and flight.departure_datetime between  %s and %s 
        group by flight.flight_num, flight.airline_name, flight.departure_datetime, flight.arrival_datetime, flight.status, flight.base_price, airplane.num_seats
    '''

    cursor.execute(query, (departure_airport_ids, arrival_airport_ids, departure_date, departure_midnight))
    departure_flights = cursor.fetchall()

    # Convert all datetimes to string so that it gets easier to display on html 
    for flight in departure_flights:
        flight['departure_datetime'] = str(flight['departure_datetime'])
        flight['arrival_datetime'] = str(flight['arrival_datetime'])
        # Also add a new datapoint, time
        flight['departure_time'] = flight['departure_datetime'][11:16]
        flight['arrival_time'] = flight['arrival_datetime'][11:16]
        flight['remaining_tickets'] = flight['num_seats'] - flight['Ticket_Count']

    print('Departure Flights: ', departure_flights)

    return render_template('searchResults.html', flights = departure_flights, cities = [departure_city, arrival_city]) 

# all flights
def staff_view_flights(airline_name):
    cursor = conn.cursor()
    query = 'SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code FROM flight WHERE flight.airline_name = %s'
    cursor.execute(query, (airline_name))
    data = cursor.fetchall()
    print(data)
    return data

def staff_view_flights_30_days(airline_name):
    cursor = conn.cursor()
    query = 'SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code FROM flight WHERE flight.airline_name = %s AND (flight.departure_datetime BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 30 DAY))'
    cursor.execute(query, (airline_name))
    data = cursor.fetchall()
    print(data)
    return data

def getStaffPhone(username):
    cursor = conn.cursor()
    query = 'SELECT phone_number FROM staff_phone WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    print(data)
    return data

@app.route('/logout')
def logout():
    if session['role'] == 'staff':
        session.pop('username',None)
        session.pop('role',None)
        session.pop('airline',None)
        session.pop('login',None)
    else:
        session.pop('email', None)
        session.pop('name', None)
    return render_template('index.html')



#========================================================================
if __name__ == "__main__":
    app.run(debug=True)

