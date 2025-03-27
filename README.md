# IS3107-group11
IS3107 Group 11

# Backend

### You only need to do the following once when you first pull

1. create a venv
```bash
python -m venv venv
```

2. start virtual environment
```bash
source venv/bin/activate
```

3. install dependencies
```bash
pip install -r requirments.txt
```

### To start Airflow

1. Open a terminal in the backend directory, make sure venv is activated 
```bash
cd backend
source venv/bin/activate
```

2. Startup the airflow standalone
```bash
airflow standalone
```

3. Access on browser, password in telegram
```bash
localhost:8080
```

4. Deactivate when done
```bash
deactivate
```


### To run the backend and test the endpoints

1. Open a NEW terminal in the backend directory, make sure venv is activated 
```bash
cd backend
source venv/bin/activate
```

2. run the backend
```bash
uvicorn main:app --reload
```

3. open the endpoint interface in browser
```bash
http://127.0.0.1:8000/docs
```



# Frontend
```bash
cd frontend
```

1. install packages
```bash
npm install
```

2. run scripts and open in browser
```bash
npm run start
```
