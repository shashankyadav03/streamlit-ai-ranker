import streamlit as st
import pandas as pd
import io
import logging
import requests
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize session state for DataFrame
if 'df' not in st.session_state:
    st.session_state.df = None

# Function to normalize location
def normalize_location(location):
    if pd.isna(location):
        return "Unknown"
    location = location.lower()
    location = re.sub(r'\d+', '', location)  # Remove numbers
    location = re.sub(r'[^\w\s]', '', location)  # Remove special characters
    location = location.strip()

    # Define keyword to standard location mapping
    location_mappings = {
        'delhi': ['delhi', 'new delhi', 'ncr', 'shahjahanpur'],
        'mumbai': ['mumbai', 'bombay'],
        'chennai': ['chennai', 'madras'],
        'bangalore': ['bangalore', 'bengaluru'],
        'kolkata': ['kolkata', 'calcutta'],
        'hyderabad': ['hyderabad'],
        'ahmedabad': ['ahmedabad'],
        'jaipur': ['jaipur']
    }

    for standard, variants in location_mappings.items():
        if any(variant in location for variant in variants):
            return standard.capitalize()
    return location  # Return original if no match found

# Function to normalize disability
def normalize_disability(disability):
    if pd.isna(disability) or disability.strip() == "":
        return "None"
    disability = disability.lower()
    disability = re.sub(r'\d+%', '', disability)  # Remove percentage
    disability = re.sub(r'[^\w\s]', '', disability)  # Remove special characters
    disability = disability.strip()

    # Define keyword to standard disability mapping
    disability_mappings = {
        'locomotor': ['locomotor', 'locomotor disability', 'locomotor can work'],
        'blindness': ['blindness', 'blind'],
        'low vision': ['low vision', 'vision impairment'],
        'hearing impairment': ['hearing impairment', 'deaf', 'hard of hearing'],
        'intellectual disability': ['intellectual disability', 'learning disability']
    }

    for standard, variants in disability_mappings.items():
        if any(variant in disability for variant in variants):
            return standard.capitalize()
    return disability  # Return original if no match found

# Function to normalize educational qualification
def normalize_education(education):
    if pd.isna(education):
        return "Unknown"
    education = education.lower()
    education = re.sub(r'[^\w\s]', '', education)  # Remove special characters
    education = education.strip()

    education_mappings = {
        'high school': ['10th pass', '12th pass', 'high school', 'secondary'],
        'bachelors': ['bachelors', 'bachelor'],
        'masters': ['masters', 'master'],
        'phd': ['phd', 'doctorate', 'doctoral']
    }

    for standard, variants in education_mappings.items():
        if any(variant in education for variant in variants):
            return standard.capitalize()
    return education  # Return original if no match found

# Function to normalize work experience
def normalize_experience(exp):
    if pd.isna(exp) or exp == "":
        return 0.0
    try:
        return float(exp)
    except ValueError:
        match = re.match(r'(\d+\.?\d*)', exp)
        if match:
            return float(match.group(1))
        return 0.0

# Streamlit app setup
st.set_page_config(page_title="Candidate Finder", layout="wide")

# Sidebar setup
st.sidebar.title("Candidate Finder")

# User inputs
job_description = st.sidebar.text_area("Job Description", height=100, placeholder="Enter the job description here...")
n_candidates = st.sidebar.number_input("Page Number", min_value=1, max_value=50, value=1)
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
            # Check if token is provided
            if not token:
                st.error("Error: Please provide a valid DataFinSight token.")
                st.stop()

            # Check if job description and number of candidates are provided
            if not job_description or not n_candidates:
                st.error("Error: Please provide a valid job description and number of candidates.")
                st.stop()

            try:
                # Extract candidates
                # Make the POST request to the Azure Function
                response = requests.post("https://datafinsight.azurewebsites.net/api/ai_search?code={}".format(token), json=data)
                response.raise_for_status()
                response_json = response.json()
                candidates = response_json.get("candidates")
            
                # Check if candidates exist
                if candidates:
                    try:
                        # Convert the list of candidates to a DataFrame
                        df = pd.DataFrame(candidates)
            
                        # Normalize the relevant fields
                        df['location_preference'] = df['location_preference'].apply(normalize_location)
                        df['disability'] = df['disability'].apply(normalize_disability)
                        df['educational_qualification'] = df['educational_qualification'].apply(normalize_education)
                        df['work_experience'] = df['work_experience'].apply(normalize_experience)

                        # Drop email column
                        df.drop(columns=['email'], inplace=True)
            
                        # Store DataFrame in session state
                        st.session_state.df = df
            
                        st.success("Candidates found!")
            
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                else:
                    st.error("Error: No candidates found.")
            except Exception as e:
                st.error(f"An error occurred during the request: {str(e)}")

# If DataFrame is available, display filters and data
if st.session_state.df is not None:
    df = st.session_state.df

    # Extract unique values for filters
    locations = df['location_preference'].dropna().unique()
    disabilities = df['disability'].dropna().unique()
    educations = df['educational_qualification'].dropna().unique()

    # Sidebar filters
    st.sidebar.subheader("Filters")

    # Extract unique values for filters
    locations = df['location_preference'].dropna().unique()
    disabilities = df['disability'].dropna().unique()
    educations = df['educational_qualification'].dropna().unique()

    # Sidebar filters (initially empty selections)
    selected_locations = st.sidebar.multiselect("Location", options=locations)
    selected_disabilities = st.sidebar.multiselect("Disability", options=disabilities)
    selected_educations = st.sidebar.multiselect("Education Qualification", options=educations)
    work_exp_min, work_exp_max = st.sidebar.slider("Work Experience Range (Years)", 0, 30, (0, 30))

    # Apply filter button
    apply_filter = st.sidebar.button("Apply Filters")

    # Filter DataFrame only if "Apply Filters" button is clicked
    if apply_filter:
        filtered_df = df[
            (df['location_preference'].isin(selected_locations) if selected_locations else True) &
            (df['disability'].isin(selected_disabilities) if selected_disabilities else True) &
            (df['educational_qualification'].isin(selected_educations) if selected_educations else True) &
            (df['work_experience'] >= work_exp_min) &
            (df['work_experience'] <= work_exp_max)
        ]
        st.write(f"Displaying {len(filtered_df)} candidates:")
        st.dataframe(filtered_df)
    else:
        # Display all data initially if no filters are applied
        st.write("Displaying all candidates:")
        st.dataframe(df)

    # Download filtered or full data
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        (filtered_df if apply_filter else df).to_excel(writer, index=False, sheet_name='Candidates')
    excel_data = output.getvalue()

    st.download_button(
        label="Download Data as Excel",
        data=excel_data,
        file_name="candidates.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    # Main section for displaying instructions when no data is loaded
    st.markdown("""
        <style>
            .centered-heading {
                text-align: center;
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .centered-subheading {
                text-align: center;
                font-size: 1em;
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
