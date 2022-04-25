from flask import Flask, render_template, session, request, redirect, url_for
import pymysql
import hashlib
from datetime import datetime, timedelta
import json
import ast

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

months_dic = {
    1 : 'January',
    2 : 'Februray',
    3 : 'March',
    4 : 'April',
    5 : 'May',
    6 : 'June',
    7 : 'July',
    8 : 'August',
    9 : 'September',
    10 : 'October',
    11 : 'November',
    12 : 'December'
}


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
        return redirect(url_for('customerHomePage'))
    cursor = conn.cursor()
    query = 'SELECT username FROM airline_staff WHERE first_name="Leo"'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    return render_template('index.html', staff = data)


################################### Customer's Functions ########################################
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

    total = float(flight['base_price'])

    if (request.args.get('return_flight')):
        return_flight = request.args.get('return_flight')
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
        return render_template('purchaseTickets.html', flight = flight, flight2 = flight2, total = total)

    cursor.close()
    return render_template('purchaseTickets.html', flight = flight, total = total)

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

    flight_num2 = request.args.get('flight_num2')
    departure_datetime2 = request.args.get('departure_datetime2')
    sold_price2 = request.args.get('sold_price2')
    airplane_id2 = request.args.get('airplane_ID2')
    airline_name2 = request.args.get('airline_name2')

    email = session['email']
    purchase_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()

    try:
        query = 'INSERT INTO ticket(email, airplane_ID, airline_name, flight_num, departure_datetime, sold_price, card_number, name_on_card, card_type, expiration_date, purchase_datetime) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (email, airplane_id1, airline_name1, flight_num1, departure_datetime1, sold_price1, card_number, name_on_card, card_type, expiration_date, purchase_datetime))
        conn.commit()
        cursor.execute(query, (email, airplane_id2, airline_name2, flight_num2, departure_datetime2, sold_price2, card_number, name_on_card, card_type, expiration_date, purchase_datetime))
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
    purchase_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()

    try:
        query = 'INSERT INTO ticket(email, airplane_ID, airline_name, flight_num, departure_datetime, sold_price, card_number, name_on_card, card_type, expiration_date, purchase_datetime) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (email, airplane_id, airline_name, flight_num, departure_datetime, sold_price, card_number, name_on_card, card_type, expiration_date, purchase_datetime))
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
    print(flight_num)
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

    cities = [departure_city, arrival_city]


    return render_template('selectReturnFlight.html', flights=arrival_flights, cities=cities, selected_departure_flight_id = selected_departure_flight_id, flight1_price=flight1_price)

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

    print(departure_date)
    print(departure_airport_ids)


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


    round_trip = False
    if (type_of_trip == "round_trip"):
        round_trip = True

    return render_template('searchResults.html', 
                            flights = {'departure': departure_flights, 'arrival' : arrival_flights}, 
                            cities = [departure_city, arrival_city], 
                            round_trip = round_trip, 
                            arrival_date = arrival_date) 



@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('name', None)
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)

