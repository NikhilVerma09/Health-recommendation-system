import streamlit as st
import pandas as pd

# --- Data Loading ---
# This function loads hospital data from the external CSV file.
def get_hospital_data():
    """Loads hospital data from a CSV file."""
    try:
        # Assumes 'hospital_data.csv' is in the same directory as the script.
        return pd.read_csv('hospital_data.csv')
    except FileNotFoundError:
        st.error("`hospital_data.csv` not found. Please make sure the data file is in the same directory as the app.")
        # Return an empty DataFrame with the correct columns to prevent the app from crashing.
        return pd.DataFrame({
            'hospital_name': [], 'doctor_availability': [], 'waiting_time': [],
            'distance': [], 'reviews': [], 'expense_score': []
        })

def rank_hospitals(df, situation):
    """
    Ranks hospitals based on a weighted score according to the user's situation.
    The function normalizes data to ensure fair scoring across different metrics.
    """
    weights = {
        'Urgent Care': {
            'distance': -0.4,
            'waiting_time': -0.3,
            'doctor_availability': 0.2,
            'reviews': 0.05,
            'expense_score': 0.05
        },
        'High-Quality Focus': {
            'reviews': 0.4,
            'doctor_availability': 0.3,
            'waiting_time': -0.15,
            'distance': -0.1,
            'expense_score': 0.05 # Willing to tolerate higher expense for quality
        },
        'Balanced Approach': {
            'reviews': 0.2,
            'distance': -0.2,
            'expense_score': -0.2,
            'doctor_availability': 0.2,
            'waiting_time': -0.2
        }
    }
    current_weights = weights[situation]
    normalized_df = df.copy()

    for col, weight in current_weights.items():
        min_val = df[col].min()
        max_val = df[col].max()
        if (max_val - min_val) == 0:
            normalized_df[col] = 0.5
            continue
        if weight < 0:
            normalized_df[col] = (max_val - df[col]) / (max_val - min_val)
        else:
            normalized_df[col] = (df[col] - min_val) / (max_val - min_val)
    df['score'] = (
        normalized_df['distance'] * abs(current_weights.get('distance', 0)) +
        normalized_df['waiting_time'] * abs(current_weights.get('waiting_time', 0)) +
        normalized_df['doctor_availability'] * abs(current_weights.get('doctor_availability', 0)) +
        normalized_df['reviews'] * abs(current_weights.get('reviews', 0)) +
        normalized_df['expense_score'] * abs(current_weights.get('expense_score', 0))
    )
    return df.sort_values(by='score', ascending=False).reset_index(drop=True)


# --- Streamlit UI ---
st.set_page_config(layout="wide")

st.title('🏥 Smart Hospital Ranking System')
st.markdown("""
This application helps you find the best hospital for your specific needs. 
Select your situation from the sidebar, and the model will rank nearby hospitals by dynamically adjusting the importance of factors like distance, waiting time, cost, and reviews.
""")


st.sidebar.header('Tell us your situation:')
situation = st.sidebar.selectbox(
    'What is your primary concern?',
    (
        'Urgent Care', 
        'High-Quality Focus', 
        'Balanced Approach'
    ),
    index=2, # Default to 'Balanced Approach'
    help="""
    Select the option that best matches your needs:
    - **Urgent Care**: Prioritizes shortest distance and waiting time.
    - **High-Quality Focus**: Prioritizes best reviews and doctor availability.
    - **Balanced Approach**: Provides a general ranking with no single strong priority.
    """
)

# --- Main Page Display ---
hospital_df = get_hospital_data()

# Only proceed if the dataframe is not empty
if not hospital_df.empty:
    ranked_hospitals = rank_hospitals(hospital_df.copy(), situation)

    st.header(f"Top Hospital Recommendations for: `{situation}`")

    # Display ranked results
    for index, row in ranked_hospitals.iterrows():
        rank = index + 1
        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**#{rank}**"
        
        with st.container():
            st.markdown(f"---")
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.markdown(f"<div style='font-size: 2.5em; text-align: center; margin-top: 20px;'>{emoji}</div>", unsafe_allow_html=True)

            with col2:
                st.subheader(f"{row['hospital_name']}")
                
                # Display metrics with icons using smaller custom markdown
                c1, c2, c3, c4, c5 = st.columns(5)
                
                # Column 1: Distance
                c1.markdown(f"""
                <div title="Lower is better">
                    <p style="font-size:0.9rem; margin-bottom:-5px; opacity:0.7;">Distance</p>
                    <p style="font-size:1.1rem; font-weight:600;">{row['distance']} km</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Column 2: Waiting Time
                c2.markdown(f"""
                <div title="Lower is better">
                    <p style="font-size:0.9rem; margin-bottom:-5px; opacity:0.7;">Waiting Time</p>
                    <p style="font-size:1.1rem; font-weight:600;">{row['waiting_time']} min</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Column 3: Expense
                c3.markdown(f"""
                <div title="Lower score is cheaper">
                    <p style="font-size:0.9rem; margin-bottom:-5px; opacity:0.7;">Expense</p>
                    <p style="font-size:1.1rem; font-weight:600;">{row['expense_score']}/10</p>
                </div>
                """, unsafe_allow_html=True)

                # Column 4: Reviews
                c4.markdown(f"""
                <div title="Higher is better">
                    <p style="font-size:0.9rem; margin-bottom:-5px; opacity:0.7;">Reviews</p>
                    <p style="font-size:1.1rem; font-weight:600;">{row['reviews']} ⭐</p>
                </div>
                """, unsafe_allow_html=True)

                # Column 5: Doctors On-call
                c5.markdown(f"""
                <div title="Higher availability is better">
                    <p style="font-size:0.9rem; margin-bottom:-5px; opacity:0.7;">Doctors On-call</p>
                    <p style="font-size:1.1rem; font-weight:600;">{row['doctor_availability']}/10</p>
                </div>
                """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Original Unranked Data")
    st.sidebar.dataframe(hospital_df)


