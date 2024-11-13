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
## Here is how I solved the tasks.
### Task1:
- After getting the query parameter for the sales_rep_id, I use a dataframe to filter data so that I get a new dataframe with only that employee's data.
- Then I simply pass that to an llm and it generated the output.
### Task2: 
- I broke the dataframe into 10 parts as we cannot provide the entire dataframe to the llm due to token restrictions. I pass each dataframe from the 10 dataframes to an llm to generate a summary.
- I also use pandas built-in functions to get the statistics of the entire data, I later pass the summaries of all the data frames and the statistics to an llm which generates the overall summary.
### Task3:
- I separated the dataframe based on months such that each dataframe consists of the data of a particular month. I then use an llm and pass this data to the llm which generates the trends, forcasting and analysis of the months.
- For quaterly analyis, I merge every datafames together to get a new data which consists of a single quartile. I then pass that data for each quartile to get the respected analysis.
