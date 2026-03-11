import streamlit as st
import pandas as pd
from pymongo import MongoClient

# --- 1. App Configuration ---
st.set_page_config(page_title="Contact Categorizer", page_icon="📇", layout="centered")
st.markdown("""<style>div.row-widget.stRadio > div { flex-direction:row; flex-wrap: wrap; gap: 10px; }</style>""", unsafe_allow_html=True)

INPUT_FILE = "unknown_contacts_app.csv"

# --- 2. Database Connection ---
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["MONGO_URI"])

client = init_connection()
db = client.CoutureDB
collection = db.UnknownContactsLabeled 

# --- 3. Data Loading & Smart Resume ---
@st.cache_data
def load_data():
    return pd.read_csv(INPUT_FILE)

df_input = load_data()
total_contacts = len(df_input)

labeled_count = collection.count_documents({})
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = labeled_count

# --- 4. The User Interface ---
st.title("Contact Categorizer 📇")
st.progress(st.session_state.current_idx / total_contacts if total_contacts > 0 else 0)
st.caption(f"Progress: {st.session_state.current_idx} out of {total_contacts} completed")

if st.session_state.current_idx < total_contacts:
    contact = df_input.iloc[st.session_state.current_idx]
    
    # --- NAVIGATION BUTTONS ---
    nav_col1, nav_col2 = st.columns(2)
    go_back = False
    submit_next = False
    
    with nav_col1:
        if st.session_state.current_idx > 0:
            go_back = st.button("⬅️ GO BACK", use_container_width=True)
            
    with nav_col2:
        submit_next = st.button("💾 SUBMIT & NEXT", type="primary", use_container_width=True)

    st.write("---")
    
    # --- DISPLAY INFO ---
    display_name = contact.get('Display Name', 'Unknown')
    st.success(f"**👤 {display_name}**")
        
    st.write("---")
    
    # --- CATEGORY SELECTION ---
    category_options = [
        "Don't know", "Service Provider", "Client", "Enquiry", "Bridal Asia", 
        "Procurement", "M&K", "Instagram", "Assistant", "Waters Edge", 
        "BVRTSE", "Buddhism Group", "Stylist", "Masterji", "MAAHEIR", 
        "IIM", "Family", "Model", "LADIES WHO LEAD", "Hotshot"
    ]
    selected_category = st.radio("Select Category:", category_options, index=0)
    custom_category = st.text_input("✍️ Or type a custom category here (overrides radio selection):")
    
    st.write("---")
    
    # --- NEW: ADDITIONAL DETAILS ---
    st.markdown("**📝 Additional Details**")
    
    # Smart Pre-fill: If the original CSV had an Organization Name, pre-fill the box with it!
    existing_org = str(contact.get('Organization Name', ''))
    if existing_org.lower() == 'nan' or existing_org.lower() == 'no org provided':
        existing_org = ""
        
    new_org_name = st.text_input("🏢 Organization Name", value=existing_org)
    new_org_title = st.text_input("💼 Organization Title")
    gender = st.radio("⚧️ Gender", ["Not sure", "M", "F"], index=0)

    # --- ACTION LOGIC ---
    if go_back:
        last_contact = df_input.iloc[st.session_state.current_idx - 1]
        collection.delete_one({"Contact_ID": last_contact['Contact_ID']})
        st.session_state.current_idx -= 1
        st.rerun()
        
    if submit_next:
        final_category = custom_category.strip() if custom_category.strip() != "" else selected_category
        
        payload = contact.to_dict()
        payload['Category'] = final_category
        
        # Add the new data into the payload!
        payload['Organization Name'] = new_org_name.strip()
        payload['Organization Title'] = new_org_title.strip()
        payload['Gender'] = gender
        
        collection.insert_one(payload)
        st.session_state.current_idx += 1
        st.rerun()

else:
    st.balloons()
    st.success("🎉 All contacts categorized! Great job.")

# --- 5. Admin Panel ---
st.sidebar.title("🛠️ Admin Panel")
current_db_count = collection.count_documents({})
st.sidebar.success(f"✅ {current_db_count} contacts safely categorized in Cloud Database.")

if current_db_count > 0:
    cursor = collection.find({}, {'_id': False}) 
    cloud_df = pd.DataFrame(list(cursor))
    
    st.sidebar.download_button(
        label="📥 Download Labeled CSV",
        data=cloud_df.to_csv(index=False).encode('utf-8'),
        file_name="final_categorized_contacts.csv",
        mime="text/csv"
    )