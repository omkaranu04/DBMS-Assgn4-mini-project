-- Household table
CREATE TABLE Household (
    House_No VARCHAR(20) PRIMARY KEY,
    Address TEXT NOT NULL
);

-- Citizens table
CREATE TABLE Citizens (
    Aadhar_No VARCHAR(12) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    DOB DATE NOT NULL,
    Gender VARCHAR(10) CHECK (Gender IN ('Male', 'Female', 'Other')),
    House_No VARCHAR(20) REFERENCES Household(House_No),
    Phone_No VARCHAR(15),
    Email_Id VARCHAR(100),
    Education_Level VARCHAR(20) CHECK (Education_Level IN ('Uneducated', 'High school', 'Sec School', 'Graduate', 'Post-graduate')),
    Income NUMERIC,
    Employment VARCHAR(20) CHECK (Employment IN ('Unemployed', 'Employee', 'Worker', 'Self-employee', 'Business')),
    Is_Alive BOOLEAN DEFAULT TRUE
);

-- Taxation table
CREATE TABLE Taxation (
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Tax_Amount NUMERIC NOT NULL,
    Payment_Status VARCHAR(10) CHECK (Payment_Status IN ('Paid', 'Unpaid', 'Partial')),
    PRIMARY KEY (Aadhar_No)
);

-- Certificates table
CREATE TABLE Certificates (
    Certificate_ID SERIAL PRIMARY KEY,
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Certificate_Type VARCHAR(20) CHECK (Certificate_Type IN ('Birth', 'Death', 'Caste')),
    Date_of_Issue DATE NOT NULL
);

-- Agricultural_Land table
CREATE TABLE Agricultural_Land (
    Land_ID SERIAL PRIMARY KEY,
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Area_in_Acres NUMERIC NOT NULL,
    Crop_Type VARCHAR(20) CHECK (Crop_Type IN ('Rice', 'Wheat', 'Sugarcane', 'Cotton', 'Jute', 'Maize', 'Millets', 'Pulses', 'Mustard', 'Groundnut')),
    Soil_Type VARCHAR(20) CHECK (Soil_Type IN ('Alluvial', 'Black', 'Red', 'Laterite'))
);

-- Health_CheckUp table
CREATE TABLE Health_CheckUp (
    CheckUp_ID SERIAL PRIMARY KEY,
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Medical_Condition TEXT,
    Prescription TEXT,
    Date_of_Visit DATE NOT NULL
);

-- Resources table
CREATE TABLE Resources (
    Resource_ID SERIAL PRIMARY KEY,
    Resource_Name VARCHAR(20) CHECK (Resource_Name IN ('Roads', 'Drainage system', 'Water')),
    Last_Inspected_Date DATE
);

-- Complaints table
CREATE TABLE Complaints (
    Complaint_ID SERIAL PRIMARY KEY,
    Resource_ID INTEGER REFERENCES Resources(Resource_ID),
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Complaint_Desc TEXT NOT NULL,
    Complain_Date DATE NOT NULL
);

-- Welfare_Schemes table
CREATE TABLE Welfare_Schemes (
    Scheme_ID SERIAL PRIMARY KEY,
    Scheme_Type VARCHAR(100) NOT NULL,
    Budget NUMERIC NOT NULL,
    Description TEXT
);

-- Avails table (junction table for Citizens and Welfare_Schemes)
CREATE TABLE Avails (
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Scheme_ID INTEGER REFERENCES Welfare_Schemes(Scheme_ID),
    Avail_Date DATE NOT NULL,
    PRIMARY KEY (Aadhar_No, Scheme_ID)
);

-- Government_Institutions table
CREATE TABLE Government_Institutions (
    Institute_ID SERIAL PRIMARY KEY,
    Institute_Type VARCHAR(20) CHECK (Institute_Type IN ('education', 'hospital', 'banking', 'administrative offices')),
    Institute_Name VARCHAR(100) NOT NULL,
    Location TEXT NOT NULL
);

-- Meetings table
CREATE TABLE Meetings (
    Meeting_ID SERIAL PRIMARY KEY,
    Date_Conducted DATE NOT NULL,
    Meeting_Agenda TEXT
);

-- Panchayat_Users table
CREATE TABLE Panchayat_Users (
    Username VARCHAR(50) PRIMARY KEY,
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Password VARCHAR(100) NOT NULL,
    Designation VARCHAR(50) CHECK (Designation IN ('Adhyaksha', 'Upadhyaksha', 'Sarpanch', 'Panch'))
);
