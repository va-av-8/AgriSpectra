# AgriSpectra

## Description
AgriSpectra is a simple ml service for maize growing stage, damage type and damage extent predictions.     
Web interface 
Functionality:    
- main page with service description    
- registration   
- autorisation   
- balance operations (top up, check, without acquiring)
- predictions of maize growing stage, damage type and damage extent based on mobile phone photos
- history checking (transactions, predictions)


## Project Structure
app/  
|--models/      
|--services/   
|--database/   
|__routes/  
|--tests/   
|--webui/   
|__workers/   

models - core entities used in all layers of application      
services - business logic    
database - schema and database logic     
routes - api routes      
tests - unit tests, perform into started container      
webui - streamlit app front     
workers - connection to RMQ and RMQ worker

Pretrined ML models downloads from WandB inside worker. 
Uploaded images saved in MinIO bucket.

## Installation
Steps:
1. git pull - get all project code      
2. Create .env files, using names for variables exactly as in .evn.template files for each folder, where it is.
3. docker compose build    
4. docker compose up    

## Usage
1. Web UI available at: http://0.0.0.0:8501/
2. API docs available at: http://localhost/docs#/
3. RabbitMQ available at: http://localhost:15672/
4. MINIO buckets available at: http://0.0.0.0:9000/

## Support
For any additional information you can mail to: anastasija.gapeeva@gmail.com

## Project status
Ongoing. UI improvements will be added during nex two weeks. Satellite data will be added during next 3 weeks. 
