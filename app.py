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
app.config['DB_PASSWORD'] = "Adayinthelife885?"
app.config['APP_DB'] = "final_project"
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


def getRangeOfMonthsWithRange(endDate, range_of_months):
    months = [] 

    for j in range(range_of_months):
        months.append(endDate - timedelta(days = 30*j))

    months.sort()

    return months

def getRangeOfMonthsWithDates(startDate, endDate):
    months = [] 
    startDate = datetime.strptime(startDate, '%Y-%m-%d')
    endDate = datetime.strptime(endDate, '%Y-%m-%d')
    while (startDate <= endDate):
        months.append(str(startDate))
        startDate = startDate + timedelta(days = 30)
    return months

def getMonthFromDateTime(datetime):
    return str(datetime)[5:7]

def getYearFromDateTime(datetime):
    return str(datetime)[:4]

def getDefaultCustomerSpendings(email, today, n_months_before, num_months):
    cursor = conn.cursor()
    query = 'SELECT * from ticket WHERE email = %s AND purchase_datetime < %s AND purchase_datetime >= %s'
    cursor.execute(query, (email, today, n_months_before[0]))
    data = cursor.fetchall()
    num_trips = len(data)
    total_money_spent = 0

    spending_eachMonth = [0] * num_months

    for ticket in data:
        for i in range(len(n_months_before)):
            if ((getMonthFromDateTime(ticket['purchase_datetime']) == getMonthFromDateTime(n_months_before[i]))
                and (getYearFromDateTime(ticket['purchase_datetime']) == getYearFromDateTime(n_months_before[i]))
            ):
                spending_eachMonth[i] += float(ticket['sold_price'])
        total_money_spent += float(ticket['sold_price']) 

    for i in range(len(n_months_before)):
        n_months_before[i] = str(n_months_before[i])[:7]

    return (spending_eachMonth, n_months_before, num_trips, total_money_spent)


def getLastYearData(email):
    today = datetime.today()
    last_year = today - timedelta(days = 365)

    cursor = conn.cursor()
    query = 'SELECT * FROM ticket WHERE email = %s AND purchase_datetime > %s AND purchase_datetime <= %s'
    cursor.execute(query, (email, last_year, today))
    data = cursor.fetchall() 

    num_trips = len(data)

    total_money_spent = 0 

    for flight in data:
        total_money_spent += float(flight['sold_price'])
    
    return num_trips, total_money_spent
  

@app.route('/')
def index():
    if (session):
        if (session['role'] == 'customer'):
            return redirect(url_for('customerHomePage'))
        else:
            return redirect(url_for('staffHomePage'))

    return render_template('index.html')


#=========================== Customer's Functions ============================
@app.route('/customerHomePage')
def customerHomePage():

    six_months_before = getRangeOfMonthsWithRange(datetime.today(), 6)
    today = datetime.today()
    num_months = 6 
    spending_data, months, num_trips, total_money_spent = getDefaultCustomerSpendings(session['email'], today, six_months_before, num_months)

    if (request.args.get('message')):
        message = request.args.get('message')
        return render_template('customerHomePage.html', spending_data = spending_data, months = months, num_trips = num_trips, total_money_spent=total_money_spent, message = message)

    return render_template('customerHomePage.html', spending_data = spending_data, months = months, num_trips = num_trips, total_money_spent=total_money_spent)

#### Customer Login ####
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
        if(password.hexdigest()[:20] == data['password']):
            session['email'] = email
            session['name'] = data['name']
            session['role'] = 'customer'
        return redirect(url_for('customerHomePage'))
    except:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('index.html', error=error)

#### Customer Sign-Up ####
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

### Cutsomer View Spendings Page ###
@app.route('/viewTotalSpendings', methods = ['GET', 'POST'])
def viewTotalSpendings():
    try:
        start_date_range = request.form['start_date_range']
        end_date_range = request.form['end_date_range']
    except:
        six_months_before = getRangeOfMonthsWithRange(datetime.today(), 6)
        spending_data, months, num_trips, total_money_spent = getDefaultCustomerSpendings(session['email'], datetime.today(), six_months_before, 6)
        return render_template('viewTotalSpendings.html', spending_data = spending_data, months = months, num_trips = num_trips, total_money_spent = total_money_spent) 

    months = getRangeOfMonthsWithDates(start_date_range, end_date_range)
    spending_data, months, num_trips, total_money_spent= getDefaultCustomerSpendings(session['email'], datetime.today(), months, len(months))

    return render_template('viewTotalSpendings.html', spending_data = spending_data, months = months, num_trips = num_trips, total_money_spent = total_money_spent)


@app.route('/checkFlightStatus', methods = ['GET', 'POST'])
def checkFlightStatus():
    
    airline_name = request.form['airline_name']
    flight_number = request.form['flight_number']
    departure_time = request.form['departure_time']
    datetime.strptime(departure_time, '%Y-%m-%dT%H:%M')
    arrival_time = request.form['arrival_time']
    datetime.strptime(arrival_time, '%Y-%m-%dT%H:%M')

    query = 'SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s AND (departure_datetime = %s OR arrival_datetime = %s)'

    cursor = conn.cursor()

    cursor.execute(query, (airline_name, flight_number, departure_time, arrival_time))
    
    flights = cursor.fetchall()

    print(flights)
    return render_template('flightStatus_searchResults.html', flights = flights)


#### Customer Purchase Page ####
@app.route('/purchaseTickets', methods = ['GET', 'POST'])
def purchaseTickets():

    departure_flight_id = request.args.get('departure_flight_id')
    cursor = conn.cursor()

    query = 'SELECT * FROM flight LEFT OUTER JOIN airplane ON airplane.ID = flight.airplane_ID WHERE flight.flight_num = %s'
    cursor.execute(query, (departure_flight_id))
    flight = cursor.fetchone()

    flight['departure_datetime'] = str(flight['departure_datetime'])
    flight['arrival_datetime'] = str(flight['arrival_datetime'])
    # Also add a new datapoint, time
    flight['departure_time'] = flight['departure_datetime'][11:16]
    flight['arrival_time'] = flight['arrival_datetime'][11:16]

    flight['base_price'] = request.args.get('flight1_price') 

    ticketClass = request.args.get('class')  

    total = float(flight['base_price'])

    if (request.args.get('return_flight')):
        return_flight = request.args.get('return_flight')
        ticketClass2 = request.args.get('class2')
        query = 'SELECT * FROM flight WHERE flight.flight_num = %s'
        cursor.execute(query, (return_flight))
        flight2 = cursor.fetchone()
        flight2['departure_datetime'] = str(flight2['departure_datetime'])
        flight2['arrival_datetime'] = str(flight2['arrival_datetime'])
        # Also add a new datapoint, time
        flight2['departure_time'] = flight2['departure_datetime'][11:16]
        flight2['arrival_time'] = flight2['arrival_datetime'][11:16]
        flight2['base_price'] = request.args.get('flight2_price')
        total += float(flight2['base_price'])
        cursor.close()
        return render_template('purchaseTickets.html', flight = flight, ticketClass = ticketClass, ticketClass2 = ticketClass2, flight2 = flight2, total = total)

    cursor.close()
    return render_template('purchaseTickets.html', ticketClass = ticketClass, flight = flight, total = total)

#### Customer Execute Round-Trip Purchase ###
@app.route('/executePurchaseRoundTrip', methods = ['GET', 'POST'])
def executePurchaseRoundTrip():
    name_on_card = request.form['name']
    card_number = request.form['card_number']
    card_type = request.form['card_type']
    expiration_date = request.form['expiration_date']  

    flight_num1 = request.args.get('flight_num1')
    departure_datetime1 = request.args.get('departure_datetime1')
    sold_price1 = request.args.get('sold_price1')
    airplane_id1 = request.args.get('airplane_ID1')
    airline_name1 = request.args.get('airline_name1')
    ticketClass = request.args.get('ticketClass')

    flight_num2 = request.args.get('flight_num2')
    departure_datetime2 = request.args.get('departure_datetime2')
    sold_price2 = request.args.get('sold_price2')
    airplane_id2 = request.args.get('airplane_ID2')
    airline_name2 = request.args.get('airline_name2')
    ticketClass2 = request.args.get('ticketClass2')

    email = session['email']
    purchase_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()

    try:
        query = 'INSERT INTO ticket(email, airplane_ID, airline_name, flight_num, departure_datetime, sold_price, card_number, name_on_card, card_type, expiration_date, purchase_datetime, travel_class) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (email, airplane_id1, airline_name1, flight_num1, departure_datetime1, sold_price1, card_number, name_on_card, card_type, expiration_date, purchase_datetime, ticketClass))
        conn.commit()
        cursor.execute(query, (email, airplane_id2, airline_name2, flight_num2, departure_datetime2, sold_price2, card_number, name_on_card, card_type, expiration_date, purchase_datetime, ticketClass2))
        conn.commit()
        cursor.close()
    except:
        cursor.close()
        return render_template('customerHomePage.html', error = "There was an error processing your request. Please try again.")
    
    return render_template('customerHomePage.html', message = "Congratulations! Your flight has been booked.")


#### Customer Execute One-Way Purchase ####
@app.route('/executePurchaseOneWay', methods = ['GET', 'POST'])
def executePurchaseOneWay():
    name_on_card = request.form['name']
    card_number = request.form['card_number']
    card_type = request.form['card_type']
    expiration_date = request.form['expiration_date']   
    flight_num = request.args.get('flight_num')
    departure_datetime = request.args.get('departure_datetime')
    sold_price = request.args.get('sold_price')
    airplane_id = request.args.get('airplane_ID')
    airline_name = request.args.get('airline_name')
    email = session['email']
    ticketClass = request.args.get('ticketClass')
    purchase_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()

    try:
        query = 'INSERT INTO ticket(email, airplane_ID, airline_name, flight_num, departure_datetime, sold_price, card_number, name_on_card, card_type, expiration_date, purchase_datetime, travel_class) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (email, airplane_id, airline_name, flight_num, departure_datetime, sold_price, card_number, name_on_card, card_type, expiration_date, purchase_datetime, ticketClass))
        conn.commit()
        cursor.close()    
    except:
        return redirect('customerHomePage.html', error = "There was an error processing your request. Please try again.")

    return redirect(url_for('customerHomePage', message = "Congratulations! Your flight has been booked."))

@app.route('/cancelFlight', methods = ['POST','GET'])
def cancelFlight():
    flight_num = request.args.get('flight_num')
    email = session['email']
    cursor = conn.cursor() 
    query = 'DELETE from ticket WHERE email = %s AND flight_num = %s'
    cursor.execute(query, (email, flight_num))
    conn.commit() 
    return redirect(url_for('viewMyFlights', message = "Flight cancelled successfully."))  


@app.route('/viewMyFlights', methods = ['GET', 'POST'])
def viewMyFlights():
    if not session:
        return render_template('index.html', error = "You are not authorized to view that page. Please log in to view flights.")

    email = session['email']
    
    query = 'SELECT * FROM ticket LEFT OUTER JOIN flight ON ticket.flight_num = flight.flight_num WHERE ticket.email = %s' 
    cursor = conn.cursor()

    #try:
    cursor.execute(query, (email))
    flight_data = cursor.fetchall() 
    
    upcoming_flights = []
    past_flights = [] 

    for flight in flight_data:
        query = 'SELECT * from rate WHERE email = %s AND flight_num = %s'
        cursor.execute(query, (session['email'], flight['flight_num']))
        rating_data = cursor.fetchone() 
        if (rating_data):
            flight['rating'] = str(rating_data['rating'])
            flight['comment'] = rating_data['comment']
        
        if datetime.today() + timedelta(days = 1) >= flight['departure_datetime']:
            flight['can_cancel'] = False
        else:
            flight['can_cancel'] = True

        if (flight['departure_datetime'] > datetime.now()):
            flight['departure_datetime'] = str(flight['departure_datetime'])
            flight['arrival_datetime'] = str(flight['arrival_datetime'])
            # Also add a new datapoint, time
            flight['departure_time'] = flight['departure_datetime'][11:16]
            flight['arrival_time'] = flight['arrival_datetime'][11:16]
            upcoming_flights.append(flight)
        else:
            flight['departure_datetime'] = str(flight['departure_datetime'])
            flight['arrival_datetime'] = str(flight['arrival_datetime'])
            # Also add a new datapoint, time
            flight['departure_time'] = flight['departure_datetime'][11:16]
            flight['arrival_time'] = flight['arrival_datetime'][11:16]
            past_flights.append(flight)
        

    cursor.close()

    if (request.args.get('message')):
        message = request.args.get('message')
        return render_template('viewMyFlights.html', upcoming_flights = upcoming_flights, past_flights = past_flights, message = message)

    return render_template('viewMyFlights.html', upcoming_flights = upcoming_flights, past_flights = past_flights)

    #except:
        #return render_template('index.html', error = "There was an error fetching your information. Please try again later.")


@app.route('/submitRating', methods = ['GET', 'POST'])
def submitRating():
    num_stars = request.form['number_stars']
    comments = request.form['comments']
    email = session['email']
    flight_num = request.args.get('flight_num')

    cursor = conn.cursor()
    query = 'INSERT INTO rate(flight_num, email, rating, comment) VALUES (%s, %s, %s, %s)'

    cursor.execute(query, (flight_num, email, num_stars, comments))
    conn.commit() 
    cursor.close()
    
    return render_template('index.html', message = "Successfully submitted rating.") 

@app.route('/rateMyFlight', methods = ['GET', 'POST'])
def rateMyFlight():
    
    if not session['email']:
        return render_template('index.html', error = "You are not authorized to view that page. Please log in first.")

    airline_name = request.args.get('airline_name')
    flight_num = request.args.get('flight_num')
    flight_departure_time = request.args.get('flight_departure_time')
    flight_departure_datetime = request.args.get('flight_departure_date')
    flight_departure_airport_code = request.args.get('flight_departure_airport_code')
    flight_arrival_airport_code = request.args.get('flight_arrival_airport_code')
    flight_arrival_datetime = request.args.get('flight_arrival_datetime')
    flight_arrival_time = request.args.get('flight_arrival_time')
    
    return render_template('rateMyFlight.html', airline_name = airline_name, flight_num = flight_num, flight_arrival_datetime = flight_arrival_datetime, flight_arrival_time = flight_arrival_time, flight_departure_datetime = flight_departure_datetime, flight_departure_airport_code = flight_departure_airport_code, flight_arrival_airport_code = flight_arrival_airport_code, flight_departure_time = flight_departure_time)

####################################### Staff's Functions #############################################
#============================ Staff's Functions =============================

@app.route('/staffHomePage', methods = ['GET', 'POST'])
def staffHomePage():
    if session['login'] and session['role'] == 'staff':
        username = session.get('username')
        flights = staff_view_flights(session['airline'])
        number = getStaffPhone(username)
        if (request.args.get('message')):
            message = request.args.get('message')
            return render_template("staffHomePage.html", flights = flights, number = number, username = username, message = message)
        return render_template("staffHomePage.html", flights = flights, show_button = True, username = username)
    else:
        return render_template("error.html", error = "Staff is not logged in")


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

################################### Other Functions #####################################

@app.route('/selectReturnFlight', methods = ['GET', 'POST'])
def selectReturnFlight():
    cursor = conn.cursor()
    departure_city = request.args.get('city1')
    arrival_city = request.args.get('city2')
    selected_departure_flight_id = request.args.get('selected_departure_flight_id')
    return_date = request.args.get('return_date')
    flight1_price = request.args.get('flight1_price')
    ticketClass = request.args.get('class')
    return_midnight = datetime.strptime(return_date, '%Y-%m-%d') + timedelta(days = 1)

    query = 'SELECT airport.code FROM airport WHERE airport.city = %s'
    cursor.execute(query,(departure_city))
    departure_airport_ids = cursor.fetchall()
    departure_airport_ids = tuple([id['code'] for id in departure_airport_ids])

    query = 'SELECT airport.code FROM airport WHERE airport.city = %s'
    cursor.execute(query, (arrival_city))
    arrival_airport_ids = cursor.fetchall()
    arrival_airport_ids = tuple([id['code'] for id in arrival_airport_ids])

    query2 = '''
                SELECT flight.flight_num, flight.arrival_airport_code, flight.departure_airport_code, flight.airline_name, flight.departure_datetime, flight.arrival_datetime, flight.status, flight.base_price, airplane.num_seats, COUNT(Ticket.ID_num ) as Ticket_Count  
                FROM flight  
                inner join airplane on flight.airplane_ID = airplane.ID left outer join ticket on flight.flight_num = ticket.flight_num
                WHERE flight.departure_airport_code in %s and flight.arrival_airport_code in %s and flight.departure_datetime between  %s and %s 
                group by flight.flight_num, flight.airline_name, flight.departure_datetime, flight.arrival_datetime, flight.status, flight.base_price, airplane.num_seats
                '''

    cursor.execute(query2, (arrival_airport_ids, departure_airport_ids, return_date, return_midnight))

    arrival_flights = cursor.fetchall()

    for flight in arrival_flights:
        flight['departure_datetime'] = str(flight['departure_datetime'])
        flight['arrival_datetime'] = str(flight['arrival_datetime'])
        # Also add a new datapoint, time
        flight['departure_time'] = flight['departure_datetime'][11:16]
        flight['arrival_time'] = flight['arrival_datetime'][11:16]
        flight['remaining_tickets'] = flight['num_seats'] - flight['Ticket_Count']
        if (float(flight['remaining_tickets']) <= 0.25 * float(flight['num_seats'])):
            flight['base_price'] = flight['base_price'] + 0.25 * flight['base_price']
        flight['business_price'] = flight['base_price'] + 500
        flight['firstclass_price'] = flight['base_price'] + 1000

    cities = [departure_city, arrival_city]


    return render_template('selectReturnFlight.html', flights=arrival_flights, ticketClass = ticketClass, cities=cities, selected_departure_flight_id = selected_departure_flight_id, flight1_price=flight1_price)

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
        return render_template("view_flight_staff.html", show = True, flights = data,error=None)
    else:
        return render_template("error.html", error = "User not logged in")

@app.route("/view_flight_date",methods=['GET', 'POST'])
def view_flight_date():
    if session['login'] and session['role'] == 'staff':
        if request.method == 'POST':
            cursor = conn.cursor()
            start = request.form['start time']
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
        return redirect(url_for("staffHomePage", message = "Flight Created Successfully.", show_button = True))
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
            
            query = "SELECT MONTHNAME(purchase_datetime) as month, YEAR(purchase_datetime) AS year, COUNT(ID_num) as ticket_number FROM ticket WHERE airline_name = %s AND purchase_datetime BETWEEN %s and %s GROUP BY YEAR(purchase_datetime), MONTHNAME(purchase_datetime)"
            cursor.execute(query, (airline, start_date, end_date))
            data = cursor.fetchall()
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
        return render_template('view_top_destinations.html', lastyear = lastyear, last3months = last3months)
    else:
        return render_template("error.html", error="Session fail")

#================================ Other Functions =================================

@app.route('/searchFlights', methods = ['GET', 'POST'])
def searchFlights():
    cursor = conn.cursor()
    departure_city = request.form['departure_city']
    arrival_city = request.form['arrival_city']
    departure_date = request.form['departure_date']
    type_of_trip = request.form['type_of_trip']
    arrival_date = ''
    departure_midnight = datetime.strptime(departure_date, '%Y-%m-%d') + timedelta(days = 1)
    
    if (type_of_trip == 'round_trip'):
        arrival_date = request.form['return_date']
        arrival_midnight = datetime.strptime(arrival_date, '%Y-%m-%d') + timedelta(days = 1)

    query = 'SELECT airport.code FROM airport WHERE airport.city = %s'

    cursor.execute(query,(departure_city))
    departure_airport_ids = cursor.fetchall()
    departure_airport_ids = tuple([id['code'] for id in departure_airport_ids])

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
    arrival_flights = []

    # Convert all datetimes to string so that it gets easier to display on html 
    for flight in departure_flights:
        flight['departure_datetime'] = str(flight['departure_datetime'])
        flight['arrival_datetime'] = str(flight['arrival_datetime'])
        # Also add a new datapoint, time
        flight['departure_time'] = flight['departure_datetime'][11:16]
        flight['arrival_time'] = flight['arrival_datetime'][11:16]
        flight['remaining_tickets'] = flight['num_seats'] - flight['Ticket_Count']

        if (float(flight['remaining_tickets']) <= 0.25 * float(flight['num_seats'])):
            flight['base_price'] = flight['base_price'] + 0.25 * flight['base_price']
            
        flight['business_price'] = flight['base_price'] + 500 
        flight['firstclass_price'] = flight['base_price'] + 1000 

    if (type_of_trip == 'round_trip'):
            query2 = '''
                    SELECT flight.flight_num, flight.arrival_airport_code, flight.departure_airport_code, flight.airline_name, flight.departure_datetime, flight.arrival_datetime, flight.status, flight.base_price, airplane.num_seats, COUNT(Ticket.ID_num ) as Ticket_Count  
                    FROM flight  
                    inner join airplane on flight.airplane_ID = airplane.ID left outer join ticket on flight.flight_num = ticket.flight_num
                    WHERE flight.departure_airport_code in %s and flight.arrival_airport_code in %s and flight.departure_datetime between  %s and %s 
                    group by flight.flight_num, flight.airline_name, flight.departure_datetime, flight.arrival_datetime, flight.status, flight.base_price, airplane.num_seats
                    '''
            cursor.execute(query2, (arrival_airport_ids, departure_airport_ids, arrival_date, arrival_midnight))
            arrival_flights = cursor.fetchall()
            for flight in arrival_flights:
                flight['departure_datetime'] = str(flight['departure_datetime'])
                flight['arrival_datetime'] = str(flight['arrival_datetime'])
                # Also add a new datapoint, time
                flight['departure_time'] = flight['departure_datetime'][11:16]
                flight['arrival_time'] = flight['arrival_datetime'][11:16]
                flight['remaining_tickets'] = flight['num_seats'] - flight['Ticket_Count']
                if (float(flight['remaining_tickets']) <= 0.25 * float(flight['num_seats'])):
                    flight['base_price'] = flight['base_price'] + 0.25 * flight['base_price']
                flight['business_price'] = flight['base_price'] + 500 
                flight['firstclass_price'] = flight['base_price'] + 1000 

    round_trip = False
    if (type_of_trip == "round_trip"):
        round_trip = True

    return render_template('searchResults.html', 
                            flights = {'departure': departure_flights, 'arrival' : arrival_flights}, 
                            cities = [departure_city, arrival_city], 
                            round_trip = round_trip, 
                            arrival_date = arrival_date) 


# all flights
def staff_view_flights(airline_name):
    cursor = conn.cursor()
    query = 'SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code FROM flight WHERE flight.airline_name = %s'
    cursor.execute(query, (airline_name))
    data = cursor.fetchall()
    return data

def staff_view_flights_30_days(airline_name):
    cursor = conn.cursor()
    query = 'SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code FROM flight WHERE flight.airline_name = %s AND (flight.departure_datetime BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 30 DAY))'
    cursor.execute(query, (airline_name))
    data = cursor.fetchall()
    return data

def getStaffPhone(username):
    cursor = conn.cursor()
    query = 'SELECT phone_number FROM staff_phone WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    return data

@app.route('/logout')
def logout():
    if session['role'] == 'staff':
        session.pop('username',None)
        session.pop('role',None)
        session.pop('airline',None)
        session.pop('login',None)
    else:
        session.pop('role', None)
        session.pop('email', None)
        session.pop('name', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)

