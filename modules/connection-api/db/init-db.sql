
CREATE TABLE person (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    company_name VARCHAR NOT NULL
);

CREATE TABLE connection (
    person_id INT NOT NULL,
    exposed_person_id INT NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    creation_time TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (person_id, exposed_person_id, creation_time)
);


