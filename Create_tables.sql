-- Household table
CREATE TABLE Household (
    House_No SERIAL PRIMARY KEY,
    Address TEXT NOT NULL
);

-- Citizens table 
CREATE TABLE Citizens (
    Aadhar_No VARCHAR(12) PRIMARY KEY CHECK (LENGTH(Aadhar_No) = 12 AND Aadhar_No ~ '^[1-9][0-9]{11}$'),
    Name VARCHAR(100) NOT NULL,
    DOB DATE NOT NULL,
    Gender VARCHAR(10) CHECK (Gender IN ('Male', 'Female')),
    House_No INTEGER REFERENCES Household(House_No),
    Phone_No VARCHAR(10) CHECK (LENGTH(Phone_No) = 10 AND Phone_No ~ '^[6-9][0-9]{9}$'),
    Email_Id VARCHAR(100) CHECK (Email_Id ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    Education_Level VARCHAR(20) CHECK (Education_Level IN ('Uneducated', 'High School', 'Secondary School', 'Graduate', 'Post Graduate')),
    Income NUMERIC CHECK(Income >= 0),
    Employment VARCHAR(20) CHECK (Employment IN ('Unemployed', 'Employee', 'Self Employed', 'Business')),
    Is_Alive BOOLEAN DEFAULT TRUE
);

-- Taxation table
CREATE TABLE Taxation (
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Tax_Amount NUMERIC NOT NULL DEFAULT 0,
    Payment_Status BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (Aadhar_No)
);

-- Certificates table
CREATE TABLE Certificates (
    Certificate_ID SERIAL PRIMARY KEY,
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Certificate_Type VARCHAR(20) CHECK (Certificate_Type IN ('Birth', 'Death', 'Caste', 'Domicile', 'Residence', 'Character')),
    Date_of_Issue DATE NOT NULL
);

-- Agricultural_Land table 
CREATE TABLE Agricultural_Land (
    Land_ID SERIAL PRIMARY KEY,
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Area_in_Acres INTEGER NOT NULL CHECK (Area_in_Acres > 0 AND Area_in_Acres <= 60),
    Crop_Type VARCHAR(20) CHECK (Crop_Type IN ('Rice', 'Wheat', 'Sugarcane', 'Cotton', 'Jute', 'Maize', 'Millets', 'Pulses', 'Mustard', 'Groundnut', 'Mango', 'Banana', 'Coconut', 'Vegetables', 'Sugarcane', 'Grapes')),
    Soil_Type VARCHAR(20) CHECK (Soil_Type IN ('Alluvial', 'Black', 'Red', 'Laterite', 'Peaty Soil', 'Desert Soil', 'Mountain Soil'))
);

-- Health_CheckUp table
CREATE TABLE Health_CheckUp (
    CheckUp_ID SERIAL PRIMARY KEY,
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Medical_Condition TEXT NOT NULL,
    Prescription TEXT NOT NULL,
    Date_of_Visit DATE NOT NULL
);

-- Resources table
CREATE TABLE Resources (
    Resource_ID SERIAL PRIMARY KEY,
    Resource_Name VARCHAR(20) CHECK (Resource_Name IN ('Roads', 'Drainage System', 'Water', 'Park', 'Electricity', 'Waste Management')),
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
    Scheme_Description TEXT
);

-- Avails table 
CREATE TABLE Avails (
    Aadhar_No VARCHAR(12) REFERENCES Citizens(Aadhar_No),
    Scheme_ID INTEGER REFERENCES Welfare_Schemes(Scheme_ID),
    Avail_Date DATE NOT NULL,
    PRIMARY KEY (Aadhar_No, Scheme_ID)
);

-- Government_Institutions table
CREATE TABLE Government_Institutions (
    Institute_ID SERIAL PRIMARY KEY,
    Institute_Type VARCHAR(20) CHECK (Institute_Type IN ('Educational', 'Health', 'Banking', 'Administration')),
    Institute_Name VARCHAR(100) NOT NULL,
    Institue_Location TEXT NOT NULL
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
    Designation VARCHAR(50) CHECK (Designation IN ('Sarpanch', 'Naib Sarpanch', 'Panchayat Secretary', 'Gram Sevak', 'Ward Member', 'Community Mobilizer'))
);
CREATE UNIQUE INDEX unique_sarpanch ON Panchayat_Users (Designation) WHERE Designation = 'Sarpanch';
CREATE UNIQUE INDEX unique_naib_sarpanch ON Panchayat_Users (Designation) WHERE Designation = 'Naib Sarpanch';

-- For System Administrator and Government Officials
CREATE TABLE System_Users_Top(
    Username VARCHAR(50) PRIMARY KEY,
    Password VARCHAR(100) NOT NULL,
    User_Type VARCHAR(50) CHECK (User_Type IN ('System Administrator', 'Government Official'))
);
CREATE UNIQUE INDEX unique_administrator ON System_Users_Top (User_Type) WHERE User_Type = 'System Administrator';
