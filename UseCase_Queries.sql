/*=============== Customer's Use Cases ==================*/ 






/*=============== Staff's Use Cases ==================*/ 

/* Search phone number */
SELECT phone_number FROM staff_phone WHERE username = %s
/* Add phone number */
INSERT INTO staff_phone(username, phone_number) VALUES (%s, %s)

/* 1. View flights */
/* View all flights */
SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code 
FROM flight 
WHERE flight.airline_name = %s
/* View flights in the next 30 days */
SELECT flight.flight_num, flight.airplane_ID, flight.airline_name, flight.base_price, flight.status, flight.departure_datetime, flight.departure_airport_code, flight.arrival_datetime, flight.arrival_airport_code 
FROM flight
WHERE flight.airline_name = %s AND (departure_datetime BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 30 DAY))
/* View flights based on range of dates */
SELECT * 
FROM flight 
WHERE flight.airline_name = %s  AND (flight.departure_datetime BETWEEN %s AND %s)
/* View flights based on departure airport */
SELECT * 
FROM flight 
WHERE flight.airline_name = %s  AND flight.departure_airport_code = %s
/* View flights based on arrival airport */
SELECT * 
FROM flight 
WHERE flight.airline_name = %s  AND flight.arrival_airport_code = %s

/* 2. Create New Flights */
/* search query */
SELECT flight.airplane_ID, flight.airline_name, flight.flight_num, flight.base_price, flight.status, flight.departure_datetime, flight.arrival_datetime, flight.departure_airport_code, flight.arrival_airport_code 
FROM flight
WHERE flight.airline_name = %s
/* insert query */
INSERT INTO flight(flight_num, airplane_ID, airline_name, base_price, status, departure_datetime, departure_airport_code, arrival_datetime, arrival_airport_code) 
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

/* 3. Change Status of Flight */
/* search query */
SELECT * 
FROM flight
WHERE flight.flight_num = %s AND flight.departure_datetime = %s AND flight.airline_name = %s
/* update query */
UPDATE flight SET status = %s WHERE flight_num = %s AND departure_datetime = %s

/* 4. Add Airplane in the System */
/* search query */
SELECT airplane.ID, airplane.airline_name, airplane.num_seats, airplane.manufacturer, airplane.age 
FROM airplane
WHERE airplane.airline_name = %s
/* insert query */
INSERT INTO airplane(ID, airline_name, num_seats, manufacturer, age) VALUES (%s, %s, %s, %s, %s)

/* 5. Add new airport in the system */
/* search query */
SELECT code, name, city, country, airport_type FROM airport
/* insert query */
INSERT INTO airport(code, name, city, country, airport_type) VALUES (%s, %s, %s, %s, %s)

/* 6. View Flight Ratings */
SELECT rate.flight_num, rate.email, rate.rating, rate.comment 
FROM flight, rate 
WHERE flight.airline_name = %  AND flight.flight_num = rate.flight_num 
ORDER BY rate.flight_num

/* 7. View Frequent Customers */
SELECT customer.name, customer.email 
FROM ticket, customer 
WHERE ticket.airline_name = %s AND ticket.email = customer.email 
        AND ticket.departure_datetime BETWEEN DATE_ADD(CURDATE(), INTERVAL -1 year) AND CURDATE() 
GROUP BY customer.email 
ORDER BY (count(customer.name)) DESC 

/* 8. View Reports */
SELECT MONTHNAME(purchase_datetime) AS month, YEAR(purchase_datetime) AS year, COUNT(ticket_ID) AS ticket_number 
FROM ticket 
WHERE airline_name = %s AND purchase_datetime BETWEEN %s AND %s 
GROUP BY YEAR(purchase_datetime), MONTH(purchase_datetime)

/* 9. View Earned Revenue */
/* by year */
SELECT sum(ticket.sold_price) 
FROM ticket, airline_staff 
WHERE ticket.airline_name = %s
        AND ticket.purchase_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE() 
GROUP BY airline_staff.airline_name
/* by month */
SELECT sum(ticket.sold_price) 
FROM ticket
WHERE ticket.airline_name = %s 
        AND ticket.purchase_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 month) AND CURDATE() 
GROUP BY airline_staff.airline_name

/* 10. View Earned Revenue By Travel Class */
/* first class */
SELECT sum(ticket.sold_price) 
FROM ticket 
WHERE ticket.airline_name = %s AND ticket.travel_class = 'first' 
GROUP BY ticket.airline_name
/* business class */
SELECT sum(ticket.sold_price) 
FROM ticket
WHERE ticket.airline_name = %s AND ticket.travel_class = 'business' 
GROUP BY ticket.airline_name
/* economy class */
SELECT sum(ticket.sold_price) 
FROM ticket
WHERE ticket.airline_name = %s AND ticket.travel_class = 'economy' 
GROUP BY ticket.airline_name

/* 11. View Top Destination */
/* by year */
SELECT airport.city 
FROM ticket, flight, airport 
WHERE ticket.airline_name = %s AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code 
        AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -1 year) AND CURDATE()) 
GROUP BY airport.city 
ORDER BY (count(airport.city)) DESC LIMIT 3
/* by month */
SELECT airport.city 
FROM ticket, flight, airport 
WHERE ticket.airline_name = %s AND flight.flight_num = ticket.flight_num AND flight.arrival_airport_code = airport.code 
        AND (flight.arrival_datetime BETWEEN DATE_ADD(CURDATE(),INTERVAL -3 month) AND CURDATE()) 
GROUP BY airport.city 
ORDER BY (count(airport.city)) DESC LIMIT 3
