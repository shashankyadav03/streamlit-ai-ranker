import streamlit as st
import pandas as pd
import requests
import io
import logging
import json
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logging = logging.getLogger(__name__)


# Streamlit app setup
st.set_page_config(page_title="Candidate Finder", layout="wide")

# Sidebar setup
st.sidebar.title("Candidate Finder")
st.sidebar.markdown("Use this app to find the best candidates based on a job description.")

# User inputs
job_description = st.sidebar.text_area("Job Description", height=200, placeholder="Enter the job description here...")
n_candidates = st.sidebar.number_input("Number of Candidates", min_value=1, max_value=100, value=10)
token = st.sidebar.text_input("DataFinSight Token", type="password")

# Button to trigger the search
if st.sidebar.button("Find Candidates"):
    if job_description:
        with st.spinner("Searching for the best candidates..."):
            # Prepare data for request
            data = {
                "job_description": job_description,
                "n": n_candidates
            }

            # Make request to the Azure function
            try:

                # Make the POST request to the Azure Function
                response = requests.post("https://datafinsight.azurewebsites.net/api/ai_search?code={}".format(token), json=data)
                response.raise_for_status()
                response_json = response.json()

                # convert response_json.get("candidates") to list
                candidates = response_json.get("candidates")

                # Check if candidates exist
                if candidates:
                    # Convert the list of candidates to a DataFrame
                    df = pd.DataFrame(candidates)

                    # Convert the DataFrame to a CSV string
                    csv = df.to_csv(index=False)

                    # Display success message
                    st.success("Candidates found!")

                    # Convert the CSV string to a DataFrame for displaying in the app
                    csv_df = pd.read_csv(io.StringIO(csv))

                    # Display the DataFrame in the Streamlit UI
                    st.dataframe(csv_df)

                    # Provide a download button for the CSV file
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="candidates.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Error: No candidates found.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    else:
        st.warning("Please provide a job description.")

# Main section for displaying results or instructions
st.markdown("""
    <style>
        .centered-heading {
            text-align: center;
            font-size: 2em; /* Increase the heading size */
            font-weight: bold;
            margin-bottom: 20px;
        }
        .centered-subheading {
            text-align: center;
            font-size: 1em; /* Increase the subheading size */
            margin-top: -20px;
            margin-bottom: 40px;
            line-height: 1.6;
        }
    </style>
    <h1 class='centered-heading'>AI-Powered Candidate Search</h1>
    <div class='centered-subheading'>
        This application helps you find the best candidates for your job openings using advanced AI capabilities provided by DataFinSight.
        Simply enter the job description and the number of candidates you need, and the system will rank and provide the most suitable candidates for the given job.
    </div>
""", unsafe_allow_html=True)

