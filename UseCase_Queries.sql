/*=============== Customer's Use Cases ==================*/ 






/*=============== Staff's Use Cases ==================*/ 

/* 1. View flights */
SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code 
FROM flight, airline_staff 
WHERE flight.airline_name = airline_staff.airline_name AND airline_staff.username = %s AND (departure_datetime BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 30 DAY))

/* 2. Create New Flights */
/* search query */
SELECT flight.airplane_ID, flight.airline_name, flight.flight_num, flight.base_price, flight.status, flight.departure_datetime, flight.arrival_datetime, flight.departure_airport_code, flight.arrival_airport_code 
FROM flight, airline_staff 
WHERE airline_staff.airline_name = flight.airline_name AND airline_staff.username = %s
/* insert query */
INSERT INTO flight(flight_num, airplane_ID, airline_name, base_price, status, departure_date_time, departure_airport_code, arrival_date_time, arrival_airport_code) 
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

/* 3. Change Status of Flight */
/* search query */
SELECT * 
FROM flight, airline_staff 
WHERE flight.flight_num = %s AND flight.departure_datetime = %s AND airline_staff.username = %s AND airline_staff.airline_name = flight.airline_name
/* update query */
UPDATE flight SET status = %s WHERE flight_num = %s AND departure_datetime = %s

/* 4. Add Airplane in the System */
/* search query */
SELECT airplane.ID, airplane.airline_name, airplane.num_seats, airplane.manufacturer, airplane.age 
FROM airline_staff, airplane
WHERE airline_staff.username = %s AND airline_staff.airline_name = airplane.airline_name
/* insert query */
INSERT INTO airplane(ID, airline_name, num_seats, manufacturer, age) VALUES (%s, %s, %s, %s, %s)

/* 5. Add new airport in the system */
/* search query */
SELECT code, name, city, country, airport_type FROM airport
/* insert query */
INSERT INTO airport(code, name, city, country, airport_type) VALUES (%s, %s, %s, %s, %s)

/* 6. View Flight Ratings */
SELECT rate.flight_num, rate.email, rate.rating, rate.comment 
FROM airline_staff, flight, rate 
WHERE airline_staff.username = %s AND flight.airline_name = airline_staff.airline_name AND flight.flight_num = rate.flight_num 
ORDER BY rate.flight_num

/* 7. View Frequent Customers */
SELECT customer.name, customer.email 
FROM ticket, airline_staff, customer 
WHERE airline_staff.username = %s AND ticket.airline_name = airline_staff.airline_name AND ticket.email = customer.email AND ticket.departure_datetime 
BETWEEN DATE_ADD(CURDATE(), INTERVAL -1 year) AND CURDATE() 
GROUP BY customer.email 
ORDER BY (count(customer.name)) DESC 

/* 8. View Reports */
SELECT MONTHNAME(purchase_datetime) AS month, COUNT(ticket_ID) AS ticket_number 
FROM ticket WHERE airline_name = %s AND purchase_datetime 
BETWEEN %s AND %s 
GROUP BY YEAR(purchase_datetime), MONTH(purchase_datetime)

/* 9. View Earned Revenue */
/* by year */
SELECT sum(ticket.sold_price) 
FROM ticket, airline_staff 
WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.purchase_datetime 
BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE() 
GROUP BY airline_staff.airline_name
/* by month */
SELECT sum(ticket.sold_price) 
FROM ticket, airline_staff 
WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.purchase_datetime 
BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 month) AND CURDATE() 
GROUP BY airline_staff.airline_name

/* 10. View Earned Revenue By Travel Class */
/* first class */
SELECT sum(ticket.sold_price) 
FROM ticket, airline_staff 
WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.travel_class = 'first' 
GROUP BY airline_staff.airline_name
/* business class */
SELECT sum(ticket.sold_price) 
FROM ticket, airline_staff 
WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.travel_class = 'business' 
GROUP BY airline_staff.airline_name
/* economy class */
SELECT sum(ticket.sold_price) 
FROM ticket, airline_staff 
WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND ticket.travel_class = 'economy' 
GROUP BY airline_staff.airline_name

/* 11. View Top Destination */
/* by year */
SELECT airport.city 
FROM airline_staff, ticket, flight, airport 
WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code 
        AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE()) 
GROUP BY airport.city 
ORDER BY (count(airport.city)) DESC LIMIT 3
/* by month */
SELECT airport.city 
FROM airline_staff, ticket, flight, airport 
WHERE airline_staff.username = %s AND airline_staff.airline_name = ticket.airline_name AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code 
        AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -3 month) AND CURDATE()) 
GROUP BY airport.city 
ORDER BY (count(airport.city)) DESC LIMIT 3
