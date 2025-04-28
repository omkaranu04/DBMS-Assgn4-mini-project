# Gram Panchayat Management System

The goal of this project is to build a complete web based information system having a backend database, a connectivity 
server, front end scripts and finally a form based web interface.

## Setting Up Things

Make sure that you have **psql** set up locally or at a server with necessary access rights.
You can follow this [video](https://youtu.be/tducLYZzElo?si=rZUuQx1nfU5vgpEa) for a tutorial.

Create a virtual/conda environment (recommended), and run `pip install -r requirements.txt` to install all the required dependencies.

After you have setup the **psql** by either of the ways mentioned above, you need to edit the `config.py` file to ensure proper connection to the database.

After this run the `Create_tables.sql`, to create appropriate relations and constraints to the database.

Now you are free to add the data as the relations are designed (either using psql/sql or by running the software on the go)
You can also use the [Mockaroo](https://www.mockaroo.com/) for random data generation.

## Starting the Server Locally

To start the server of this project run (before this make sure you have an active environment, if created)

```bash
  python run.py
```

Alternatively if you are using Ubuntu, you can run the makefile within the repo, to set the environment and then run the backend `run.py`

Then on the browser run the 
```bash
localhost:5000
```
