CREATE DATABASE IF NOT EXISTS weather_data;

USE weather_data;

CREATE TABLE IF NOT EXISTS countries (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    iso2_code CHAR(2) NOT NULL UNIQUE,
    iso3_code CHAR(3) NOT NULL UNIQUE,
    region VARCHAR(100),
    subregion VARCHAR(100),

    CONSTRAINT chk_iso2_code_len CHECK ( CHAR_LENGTH(iso2_code) = 2),
    CONSTRAINT chk_is3o_code_len CHECK ( CHAR_LENGTH(iso3_code) = 2)
);

CREATE TABLE IF NOT EXISTS cities (
    id CHAR(6) NOT NULL PRIMARY KEY,
    country_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(8, 5),
    longitude DECIMAL(8, 5),

    CONSTRAINT fk_city_country FOREIGN KEY (country_id) REFERENCES  countries(id),
    CONSTRAINT chk_city_id_len CHECK ( CHAR_LENGTH(id) = 6 )
);

CREATE TABLE IF NOT EXISTS weather_reading (
    date DATE NOT NULL,
    city_id CHAR(6) NOT NULL,
    main VARCHAR(50),
    description VARCHAR(200),
    temperature DOUBLE,
    feels_like DOUBLE,
    temperature_min DOUBLE,
    temperature_max DOUBLE,
    wind_speed DOUBLE,
    wind_deg DOUBLE,
    humidity INT,
    pressure INT,

    CONSTRAINT fk_weather_city FOREIGN KEY (city_id) REFERENCES cities(id),
    PRIMARY KEY (date, city_id),
    CONSTRAINT chk_weather_cityid_len CHECK ( CHAR_LENGTH(city_id) = 6 )
);

DESCRIBE countries;