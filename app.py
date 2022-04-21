from colorama import Cursor
from flask import Flask, render_template, session, request, redirect, url_for
import pymysql
import hashlib
from datetime import datetime, timedelta

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
    if session.get('login') and session.get('role') == 'staff':
        username = session.get('username')
        flights = staff_view_flights(username)
        print('flights',flights)
        return render_template("staffHomePage.html", flights = flights, show_button = True, username = username)
    else:
        return render_template("error.html", error = None)

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

@app.route('/create_new_flights')
def create_new_flights():
	if session['login'] and session['role'] == "staff" and "username" in session:
		username = session['username']
		cursor = conn.cursor()
		query = 'SELECT flight.airplane_ID, flight.airline_name, flight.flight_num, flight.base_price, flight.status, flight.departure_datetime, flight.arrival_datetime, flight.departure_airport_code, flight.arrival_airport_code FROM flight, airline_staff WHERE airline_staff.airline_name = flight.airline_name AND airline_staff.username = %s'
        # AND (flight.departure_datetime BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 30 DAY))'
		cursor.execute(query, (username))
		data = cursor.fetchall()
		cursor.close()
		return render_template('create_new_flights.html', data = data)
	else: return render_template("error.html", error = "User not logged in")
        
@app.route('/post_new_flights',methods=['GET', 'POST'])
def post_new_flights():
    if session['login'] and session['role'] == "staff" and "username" in session:
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

        query = 'INSERT INTO flight(flight_num, airplane_ID, airline_name, base_price, status, departure_date_time, departure_airport_code, arrival_date_time, arrival_airport_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (flight_num, airplane_ID, airline_name,  base_price, status, departure_datetime, departure_airport_code,arrival_datetime, arrival_airport_code))
        conn.commit()
        cursor.close()
        return redirect(url_for("create_new_flights"))
    else:
        return render_template("error.html", error="User not logged in")
        
@app.route('/add_airport')
def add_airport():
    if session['login'] and session['role'] == "staff" and "username" in session:
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
    if session['login'] and session['role'] == "staff" and "username" in session:
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
    if session['login'] and session['role'] == "staff" and "username" in session:
        username = session['username']
        cursor = conn.cursor()
        query = 'SELECT airplane.ID, airplane.airline_name, airplane.num_seats, airplane.manufacturer, airplane.age FROM airline_staff, airplane WHERE airline_staff.username = %s AND airline_staff.airline_name = airplane.airline_name'
        cursor.execute(query,(username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('add_airplane.html', data = data)
    else:
        return render_template("error.html", error = "add airplane fail")

@app.route('/post_airplane', methods=['GET', 'POST'])
def post_airplane():
    if session['login'] and session['role'] == "staff" and "username" in session:
        username = session['username']
        cursor = conn.cursor()
        query_temp = 'SELECT airline_name FROM airline_staff WHERE airline_staff.username = %s'
        cursor.execute(query_temp, (username))
        temp = cursor.fetchone()
        airline_name = temp.get('airline_name')
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
        if session['login'] and session['role'] == "staff" and "username" in session:
            cursor = conn.cursor()
            username = session['username']
            flight_num = request.form['flight_num']
            departure_datetime = request.form['departure_datetime']
            status = request.form['status']
            datetime.strptime(departure_datetime, '%Y-%m-%dT%H:%M')
            query = 'SELECT * FROM flight, airline_staff WHERE flight.flight_num = %s AND flight.departure_datetime = %s AND airline_staff.username = %s AND airline_staff.airline_name = flight.airline_name'
            cursor.execute(query,(flight_num, departure_datetime, username))
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
                return render_template('change_status.html', error = error)
        else:
            return render_template("error.html", error="Session fail")
    elif request.method == 'GET':
        return render_template('change_status.html', error = None)

# Untested Code
@app.route('/view_flight_ratings')
def view_flight_ratings():
    if session['login'] and session['role'] == "staff" and "username" in session:
        cursor = conn.cursor()
        username = session['username']
        query = 'SELECT rate.flight_num, rate.email, rate.rating, rate.comment FROM airline_staff, flight, rate WHERE airline_staff.username = %s AND flight.airline_name = airline_staff.airline_name AND flight.flight_num = rate.flight_num order by rate.flight_num'
        cursor.execute(query, (username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('view_flight_ratings.html', data=data)
    else:
        return render_template("error.html", error="Session fail")

@app.route('/view_frequent_customers')
def view_frequent_customers():
    if session['login'] and session['role'] == "staff" and "username" in session:
        cursor = conn.cursor()
        username = session['username']
        query = 'SELECT customer.name, customer.email FROM ticket, airline_staff, customer WHERE airline_staff.username = %s AND ticket.airline_name = airline_staff.airline_name AND ticket.email = customer.email AND ticket.departure_datetime BETWEEN DATE_ADD(CURDATE(), INTERVAL -1 year) AND CURDATE() GROUP BY customer.email ORDER BY (count(customer.name)) DESC '
        cursor.execute(query, (username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('view_frequent_customers.html', data=data)
    else:
        return render_template("error.html", error="Session fail")

@app.route('/view_earned_revenue')
def view_earned_revenue():
    if session['login'] and session['role'] == "staff" and "username" in session:
        cursor = conn.cursor()
        username = session['username']
        query_year = 'SELECT sum(ticket.sold_price) FROM ticket, airline_staff WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.purchase_date_time BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE() group by airline_staff.airline_name'
        query_month = 'SELECT sum(ticket.sold_price) FROM ticket, airline_staff WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.purchase_date_time BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 month) AND CURDATE() group by airline_staff.airline_name'
        cursor.execute(query_year, (username))
        lastyear = cursor.fetchone()
        cursor.execute(query_month, (username))
        lastmonth = cursor.fetchone()
        cursor.close()
        return render_template('view_earned_revenue.html', lastyear = lastyear, lastmonth = lastmonth)
    else:
        return render_template("error.html", error="Session fail")

@app.route('/view_earned_revenue_by_class')
def view_earned_revenue_by_class():
    if session['login'] and session['role'] == "staff" and "username" in session:
        cursor = conn.cursor()
        username = session['username']
        query_first = "SELECT sum(ticket.sold_price) FROM ticket, airline_staff WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.travel_class = 'first' group by airline_staff.airline_name"
        query_business = "SELECT sum(ticket.sold_price) FROM ticket, airline_staff WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.travel_class = 'business' group by airline_staff.airline_name"
        query_economy = "SELECT sum(ticket.sold_price) FROM ticket, airline_staff WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.travel_class = 'economy' group by airline_staff.airline_name"
        cursor.execute(query_first, (username))
        first = cursor.fetchone()
        cursor.execute(query_business, (username))
        business = cursor.fetchone()
        cursor.execute(query_economy, (username))
        economy = cursor.fetchone()
        cursor.close()
        return render_template('view_earned_revenue_by_class.html', first = first, business = business, economy = economy)
    else:
        return render_template("error.html", error="Session fail")

@app.route('/view_top_destinations')
def view_top_destinations():
    if session['login'] and session['role'] == "staff" and "username" in session:
        cursor = conn.cursor()
        username = session['username']
        query_year = 'SELECT airport.city FROM airline_staff, ticket, flight, airport WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE()) GROUP BY airport.city ORDER BY (count(airport.city)) DESC LIMIT 3'
        query_month = 'SELECT airport.city FROM airline_staff, ticket, flight, airport WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -3 month) AND CURDATE()) GROUP BY airport.city ORDER BY (count(airport.city)) DESC LIMIT 3'
        cursor.execute(query_year, (username))
        lastyear = cursor.fetchone()
        cursor.execute(query_month, (username))
        last3months = cursor.fetchone()
        cursor.close()
        return render_template('view_earned_revenue.html', lastyear = lastyear, last3months = last3months)
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


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('name', None)
    return render_template('index.html')

#================================ Helper Functions =================================

def staff_view_flights(username):
    cursor = conn.cursor()
    query = 'SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code FROM flight, airline_staff WHERE flight.airline_name = airline_staff.airline_name AND airline_staff.username = %s'
    # AND (departure_datetime BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 30 DAY))'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    print(data)
    return data

#========================================================================
if __name__ == "__main__":
    app.run(debug=True)

