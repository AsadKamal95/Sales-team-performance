from fastapi import FastAPI
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.output_parser import StrOutputParser

df = pd.read_csv("sales_performance_data.csv")

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")

app = FastAPI()

@app.get("/api/rep_performance/{rep_id}")
async def rep_performance(rep_id: int):
    if rep_id in df['employee_id'].values:
        filtered_df = df[df['employee_id']==rep_id]
        df_string = filtered_df.to_json()
        template = """
        You are an analyst, Provide detailed performance analysis and feedback for
        the specified sales representative. according to the provided employee_id:{id}

        Use the following data to give the analysis
        {data}
        """
        chat_prompt = ChatPromptTemplate.from_template(template=template)

        final_prompt=chat_prompt.format(
            id=id,
            data=df_string
        )

        response = llm.invoke(final_prompt)
        return response.content
    else:
        return "Employee id does not exist."

@app.get("/api/team_performance")
async def team_performance():
    df_parts = np.array_split(df, 10)
    df_string=[]
    for part in df_parts:
        df_string.append(part.to_json())
    described = df.describe()

    column_sums = df.sum(numeric_only=True).to_frame().T
    column_sums.index = ["sum"]
    description_with_sum = pd.concat([described, column_sums])
    
    prompt_template = PromptTemplate(
    input_variables=["data"],
    template="""
        You are a data analyst. Review the following data and generate a brief, structured summary containing only the essential metrics and key insights. 
        Output should be concise, without full sentences or explanations. Provide only the critical details in bullet points, as this summary will later be used 
        by another language model to generate a larger report. Use the provided example format as a guide.

        **Data to Analyze:**
        {data}

        **Generate output as follows:**
        - overall performance analysis
        - key strengths
        - areas to improve
        - top performers
        - worst performers
        Add more if you find it useful
        """
        )
    chain = prompt_template | llm | StrOutputParser()
    output=[]
    for strings in df_string:
        result = chain.invoke({"data":strings})
        output.append(result)

    employee_summaries_str = ""
    for summary in output:
        employee_summaries_str += f"Summary:\n{summary}\n\n"
    team_summary_template = """
        You are a team analyst. Below are the 10 summaries of different chunks of the entire dataset:
        {employee_summaries}

        Based on these summaries, provide an overall team performance analysis and highlight key strengths and areas for improvement.
        Please use only the provided data for KPIs as listed in {stats}, without inferring additional values or modifying any KPI numbers. 
        Report these metrics exactly as they appear.
        Example format for KPIs are as follows
        - **Total Leads Taken:** 
        - **Total Tours Booked:** 
        - **Total Applications:** 
        - **Total Revenue Confirmed:**
        - **Total Revenue Pending:** 
        - **Total Tours in Pipeline:** 
        - **Total Tours Cancelled:**
        Don't include the total number of employees.
        """
    stat_data = description_with_sum.to_json(orient="records")
    def generate_team_summary(employee_summaries_str):
        chat_prompt = ChatPromptTemplate.from_template(template=team_summary_template)
        prompt = chat_prompt.format(employee_summaries=employee_summaries_str, stats=stat_data)
        response = llm.invoke(prompt)
        
        return response.content
    team_summary = generate_team_summary(employee_summaries_str)

    return team_summary

@app.get("/api/performance_trends/{time_period}")
async def trends(time_period):
    if time_period=="monthly":
        result = monthly_data(df)
        return f"Trends for the time period: {"\n\n".join(result)}"
    elif time_period=="quaterly":
        result = quaterly_data(df)
        output = ""
        for item in result:
            output+=f"\n\n{item}"
        return f"Trends for the time period: {output}"
    else:
        return "In-correct time period provided, use monthly or quaterly only"

def monthly_data(df):
    df['dated'] = pd.to_datetime(df['dated'])
    # Fetching unique months
    temp = df['dated'].dt.to_period('M').astype(str).unique().tolist()
    unique_months=[]
    for value in temp:
        unique_months.append(value.split('-'))

    #Creating a list of dataframes. Each dataframe consist of 1 month
    monthly_data = []
    for i in range (len(unique_months)):
        year = int(unique_months[i][0])
        month = int(unique_months[i][1])

        filtered_df = df[(df['dated'].dt.year == year) & (df['dated'].dt.month == month)]
        monthly_data.append(filtered_df)

    # Getting a list of each month dataframe's statistics
    monthly_statistics = []
    for data in monthly_data:
        if 'employee_id' in data.columns:
            data.drop(columns='employee_id', inplace=True)
        described = data.describe()
        column_sums = data.sum(numeric_only=True).to_frame().T
        column_sums.index = ["sum"]
        description_with_sum = pd.concat([described, column_sums])
        monthly_statistics.append(description_with_sum)

    # Converting all the data into a list of strings
    monthly_data_string=[]
    for i, part in enumerate(monthly_data):
        monthly_data_string.append(monthly_data[i].to_json())

    # Generating every month's analysis
    
    prompt_template = PromptTemplate(
        input_variables=["data","stats"],
        template="""
            Analyze the provided sales data over the specified time period to identify trends and forecast future performance. 
            Use only the numbers from the provided statistics to ensure accuracy and consistency. 
            Output should be brief and contain only essential metrics and insights.

            ### Data:
            {data}

            ### Statistics:
            {stats}

            ### Insight Requirements:
            1. **Trends**: Highlight any significant increases, decreases, or stability in key metrics and total values.
            2. **Comparative Analysis**: Summarize any noticeable changes compared to previous periods (monthly, quarterly, or yearly).
            3. **Patterns**: Identify any seasonal effects or recurring trends.
            4. **Forecasting**: Provide a quick forecast based on observed trends, using only the statistics provided.
            5. **Recommendations**: Briefly suggest potential actions to optimize future performance or address any negative trends.

            **Output Format**: 
            - Begin with the month and year in the first line.
            - Use concise bullet points for each insight, without full sentences or explanations, as this summary will later be expanded by another model.

            **Example Output**:
            - "Month-Year"
            - Key Trends: [List of critical trends]
            - Comparative Analysis: [List of key comparisons]
            - Patterns: [List of patterns]
            - Forecast: [Forecast summary]
            - Recommendations: [Brief, actionable insights]

            **Note**: Ensure all insights are data-driven, concise, and reference only the numbers in the provided statistics.
            """
        )
    chain = prompt_template | llm | StrOutputParser()
    output=[]
    for i, strings in enumerate(monthly_data_string):
        result = chain.invoke({"data":strings, "stats": monthly_statistics[i]})
        output.append(result)
    # monthly_output = "\n".join(output)
    return output

def quaterly_data(df):

    output = monthly_data(df)

    monthly_summary_template = PromptTemplate(
    input_variables=["monthly_data"],
    template="""
    Generate a quarterly trends, analysis, and forecast summary using the monthly data provided. Use only the values from the data provided to ensure accuracy. The output should focus on essential quarterly insights, including brief forecasts, without lengthy explanations.

    ### Monthly Data:
    {monthly_data}

    ### Insight Requirements:
    1. **Quarterly Trends**: Identify significant trends for each quarter, such as growth, decline, or stability, based on aggregated monthly data.
    2. **Key Metrics**: Highlight total and average values for each quarter.
    3. **Comparative Analysis**: Compare performance between quarters, noting any increases, decreases, or stable periods.
    4. **Patterns**: Identify recurring quarterly patterns or seasonal effects.
    5. **Forecasting**: Provide a brief forecast for the next quarter based on observed trends.
    6. **Recommendations**: Offer brief action items based on quarterly insights, focusing on strategies to sustain growth or address declines.

    **Output Format**:
    - Start with the quarter name and year (e.g., "Q1 2023").
    - Provide insights in concise bullet points, including critical trends, metrics, and forecast.
    - Keep language concise to serve as input for another model generating a detailed report.
    """
)

    # Initialize the LLMChain
    chain2 = monthly_summary_template | llm | StrOutputParser()

    # Prepare the quarterly data by grouping monthly data into quarters
    #quarterly_data_strings = "\n".join(output)
    q1 = "\n".join(output[0:3])
    q2 = "\n".join(output[3:6])
    q3 = "\n".join(output[6:9])
    q4 = "\n".join(output[9:])

    quarterly_data_strings = [q1,q2,q3,q4]

    # Generate output for each quarter, including the final partial quarter if present
    output_quarterly = []
    for item in quarterly_data_strings:
        result_quarterly = chain2.invoke({"monthly_data": item})
        output_quarterly.append(result_quarterly)
    
    return output_quarterly