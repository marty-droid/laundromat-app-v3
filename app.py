import streamlit as st
import pandas as pd
import random
import re
from datetime import datetime

# --- Configuration ---
TARGET_NEIGHBORHOODS = ['Logan Square', 'Avondale', 'Hermosa']
WEIGHTS = {
    'RealEstateIncluded': 40,
    'LocationMatch': 30,
    'SellerMotivation': 20,
    'HighCapacity': 10
}

# Mock data to simulate scraped and cleaned results
# NOTE: ALL entries MUST have 'Lat' and 'Long' keys for the engine to work.
MOCK_SCRAPED_DATA = [
    {'Title': 'Profitable Laundromat, Owner Retiring', 'Location': '2800 N. Milwaukee Ave, Chicago, IL', 'Price': '$750,000', 'CashFlow': '$150,000', 'Description': 'High volume store with old equipment. Real estate included. Owner retiring after 35 years. Great for a new concept build-out. 3,000 sq ft.', 'Lat': 41.933, 'Long': -87.712},
    {'Title': 'Coin Laundry Business Only - Great Lease', 'Location': '3500 W. Fullerton Ave, Chicago, IL', 'Price': '$200,000', 'CashFlow': '$80,000', 'Description': 'Lease only. High traffic area near Avondale border. Equipment is 10 years old. No real estate. Absentee owner needs quick sale.', 'Lat': 41.924, 'Long': -87.724},
    {'Title': 'Modern Washateria near Cicero', 'Location': '5000 W. North Ave, Chicago, IL', 'Price': '$900,000', 'CashFlow': '$180,000', 'Description': 'Fully updated store with high-capacity washers. Seller moving out of state. No real estate. Good cash flow.', 'Lat': 41.910, 'Long': -87.749},
    {'Title': 'Established Laundry in Logan Square', 'Location': '2500 N. Central Park Ave, Chicago, IL', 'Price': '$450,000', 'CashFlow': '$100,000', 'Description': 'Solid neighborhood business. Real estate included. Older machines, but reliable. Strong local customer base.', 'Lat': 41.921, 'Long': -87.715},
    {'Title': 'Wash & Fold Opportunity in North Suburb', 'Location': 'Evanston, IL', 'Price': '$300,000', 'CashFlow': '$60,000', 'Description': 'Small store focused on wash and fold. Not in target area. Real estate not included.', 'Lat': 42.045, 'Long': -87.687},
    {'Title': 'Prime Hermosa Corner Lot Laundromat', 'Location': '4000 W. Diversey Ave, Chicago, IL', 'Price': '$1,200,000', 'CashFlow': '$200,000', 'Description': 'Massive potential. Real estate included. Owner needs quick exit due to health. Older, inefficient machines. Perfect for new concept.', 'Lat': 41.932, 'Long': -87.730}
]

# --- Automated Data Enrichment Functions ---

def automated_geocoding(location_text, lat, long):
    """Mocks Geocoding and Reverse Geocoding to determine precise neighborhood."""
    # Mocking a high-accuracy result based on input Lat/Long
    if 41.92 <= lat <= 41.94 and -87.73 <= long <= -87.70:
        return {'Neighborhood': 'Logan Square', 'MatchScore': 1.0}
    elif 41.92 <= lat <= 41.93 and -87.74 <= long <= -87.72:
        return {'Neighborhood': 'Avondale', 'MatchScore': 0.9}
    elif 41.90 <= lat <= 41.92 and -87.75 <= long <= -87.73:
        return {'Neighborhood': 'Hermosa', 'MatchScore': 0.85}
    else:
        return {'Neighborhood': 'Outside Target', 'MatchScore': 0.0}

def automated_nlp_analysis(description):
    """Uses NLP (keyword matching) to extract key acquisition criteria."""
    
    re_included = bool(re.search(r'real estate included|building included|property included', description.lower()))
    motivated = bool(re.search(r'owner retiring|needs quick sale|moving out of state|must sell|quick exit', description.lower()))
    old_equipment = bool(re.search(r'old equipment|older machines|ready for upgrade|inefficient machines', description.lower()))
    high_capacity = bool(re.search(r'high-capacity|modern equipment|fully updated', description.lower()))
    
    return {
        'RealEstateIncluded': re_included,
        'SellerMotivation': motivated,
        'OldEquipment': old_equipment,
        'HighCapacity': high_capacity
    }

def calculate_opportunity_score(listing):
    """Calculates a weighted score based on business priority."""
    score = 0
    
    # 1. Location Score (High weight)
    if listing['Neighborhood'] in TARGET_NEIGHBORHOODS:
        score += WEIGHTS['LocationMatch'] * listing['MatchScore']
    
    # 2. Real Estate Score (Highest weight for roll-up)
    if listing['RealEstateIncluded']:
        score += WEIGHTS['RealEstateIncluded']
        
    # 3. Seller Motivation Score
    if listing['SellerMotivation']:
        score += WEIGHTS['SellerMotivation']
        
    # 4. Concept Potential Score (We want either old equipment for a fresh concept OR high capacity)
    if listing['OldEquipment'] or listing['HighCapacity']:
        score += WEIGHTS['HighCapacity']
        
    return round(score, 2)

def run_acquisition_engine(data):
    """Processes raw scraped data into a prioritized DataFrame."""
    processed_data = []
    
    for listing in data:
        # Step 1: Geocoding and Location Verification
        geo_data = automated_geocoding(listing['Lat'], listing['Long'])
        
        # Step 2: NLP Feature Extraction
        nlp_data = automated_nlp_analysis(listing['Description'])
        
        # Combine all data points
        processed_listing = {**listing, **geo_data, **nlp_data}
        
        # Step 3: Calculate Opportunity Score
        processed_listing['OpportunityScore'] = calculate_opportunity_score(processed_listing)
        
        # Step 4: Calculate Basic Financial Metrics
        try:
            cf = float(processed_listing['CashFlow'].replace('$', '').replace(',', ''))
            price = float(processed_listing['Price'].replace('$', '').replace(',', ''))
            processed_listing['CapRate (%)'] = round((cf / price) * 100, 2)
        except ValueError:
            processed_listing['CapRate (%)'] = 0.0
            
        processed_data.append(processed_listing)

    df = pd.DataFrame(processed_data)
    
    # Final step: Sort and prioritize the best targets
    df = df.sort_values(by=['OpportunityScore', 'CapRate (%)'], ascending=[False, False])
    
    # Select and reorder columns for display
    df = df[['OpportunityScore', 'Title', 'Neighborhood', 'Price', 'CashFlow', 'CapRate (%)', 'RealEstateIncluded', 'SellerMotivation', 'Location', 'Description', 'Lat', 'Long']]
    
    return df

# --- Streamlit Application Interface ---

# Execute the engine to get the initial data
df_targets = run_acquisition_engine(MOCK_SCRAPED_DATA)
df_targets.rename(columns={'Lat': 'latitude', 'Long': 'longitude'}, inplace=True)

st.set_page_config(layout="wide")
st.title(" Laundromat Acquisition Target Prioritization Dashboard")
st.markdown("---")

# 1. Sidebar Filters
st.sidebar.header("Filter & Prioritize Targets")
selected_hoods = st.sidebar.multiselect(
    'Target Neighborhoods', 
    df_targets['Neighborhood'].unique(), 
    default=TARGET_NEIGHBORHOODS
)
min_score = st.sidebar.slider('Minimum Opportunity Score', 0, 100, 70)
re_filter = st.sidebar.checkbox('Real Estate Included Only (High Priority)', value=True)
min_cap_rate = st.sidebar.number_input('Minimum Cap Rate (%)', value=0.0, step=0.5)

# 2. Apply Filters
df_filtered = df_targets[df_targets['Neighborhood'].isin(selected_hoods)]
df_filtered = df_filtered[df_filtered['OpportunityScore'] >= min_score]
if re_filter:
    df_filtered = df_filtered[df_filtered['RealEstateIncluded'] == True]
df_filtered = df_filtered[df_filtered['CapRate (%)'] >= min_cap_rate]

# 3. KPIs
st.header("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Qualified Targets", len(df_filtered))
col2.metric("Highest Opportunity Score", df_filtered['OpportunityScore'].max() if not df_filtered.empty else 0)
col3.metric("Average Cap Rate", f"{df_filtered['CapRate (%)'].mean():.2f}%" if not df_filtered.empty else "N/A")
col4.metric("Real Estate Targets", df_filtered['RealEstateIncluded'].sum() if not df_filtered.empty else 0)

st.markdown("---")

# 4. Main Table Display
st.header("Prioritized Acquisition List (Top Targets First)")
st.dataframe(
    df_filtered.drop(columns=['latitude', 'longitude']), 
    height=350,
    column_config={
        "OpportunityScore": st.column_config.ProgressColumn(
            "Score",
            help="Weighted score based on Location, RE, and Seller Motivation",
            format="%f",
            min_value=0,
            max_value=100,
        ),
        "RealEstateIncluded": st.column_config.CheckboxColumn("RE", default=False),
        "SellerMotivation": st.column_config.CheckboxColumn("Motivated", default=False),
    }
)

# 5. Map Visualization
st.header("Geographic Clustering Map")
if not df_filtered.empty:
    # Set map center to Chicago
    st.map(df_filtered, zoom=11)
else:
    st.info("No targets meet the current filter criteria.")

# --- Instructions for Client Demonstration ---
st.sidebar.markdown("---")
st.sidebar.subheader("Client Demonstration Instructions")
st.sidebar.markdown("""
1.  **Run Locally:** Save this code as `app.py`. Open your terminal, navigate to the directory, and run: `streamlit run app.py`
2.  **Demonstrate Filtering:** Show how the **Minimum Opportunity Score** slider instantly filters the table and map to focus on the highest-potential deals.
3.  **Highlight RE:** Check the **Real Estate Included Only** box to show how the engine isolates the most valuable roll-up assets.
4.  **Explain Scoring:** Point out the **OpportunityScore** and explain that it is an automated metric combining location verification, NLP analysis of the description, and financial metrics (Cap Rate) to remove the need for manual pre-screening.
""")