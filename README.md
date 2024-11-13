# Sales-team-performance
## To run this code you need to download the required dependencies
- In terminal write pip install -r requirements.txt
- Create a .env file and add the openAI's api key. (OPENAI_API_KEY=[Your API key])
- It's a good practice to create a virtual environment for your projects, you can create one using the following command prompt
- python3 -m venv [environment name]
You need to run the main.py using the following command
uvicorn main:app --reload

To check the API using flask simply open the url provided by running the above command and add /docs at the end
You can also use postman for testing purposes.

# Note the code takes around 2 minutes to execute a request due to inference time by the model
