-- Drivers table
CREATE TABLE IF NOT EXISTS drivers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    vehicle TEXT NOT NULL,
    rating NUMERIC(2,1) CHECK (rating >= 0 AND rating <= 5)
);

-- Passengers table
CREATE TABLE IF NOT EXISTS passengers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    signup_date DATE NOT NULL
);

-- Rides table
CREATE TABLE IF NOT EXISTS rides (
    id SERIAL PRIMARY KEY,
    ride_id UUID NOT NULL UNIQUE,
    driver_id INTEGER REFERENCES drivers(id),
    passenger_id INTEGER REFERENCES passengers(id),
    request_time TIMESTAMP NOT NULL,
    pickup_time TIMESTAMP,
    dropoff_time TIMESTAMP,
    pickup_lat DOUBLE PRECISION,
    pickup_lon DOUBLE PRECISION,
    dropoff_lat DOUBLE PRECISION,
    dropoff_lon DOUBLE PRECISION,
    fare NUMERIC(6,2),
    status TEXT CHECK (status IN ('in_progress', 'completed', 'cancelled')) NOT NULL
);

-- Indexes for rides table
CREATE INDEX idx_rides_ride_id ON rides(ride_id);

-- Locations table (for route tracking)
CREATE TABLE IF NOT EXISTS ride_locations (
    id SERIAL PRIMARY KEY,
    ride_id UUID REFERENCES rides(ride_id),
    timestamp TIMESTAMP NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION
);
