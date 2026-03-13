import streamlit as st
import pandas as pd
from pymongo import MongoClient

# --- 1. App Configuration ---
st.set_page_config(page_title="Contact Categorizer", page_icon="📇", layout="centered")
# This custom CSS makes the radio buttons flow horizontally instead of a massive vertical list!
st.markdown("""<style>div.row-widget.stRadio > div { flex-direction:row; flex-wrap: wrap; gap: 10px; }</style>""", unsafe_allow_html=True)

INPUT_FILE = "unlabelled_contacts_for_app_20260313_205739.csv"

# --- 2. Database Connection ---
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["MONGO_URI"])

client = init_connection()
db = client.CoutureDB
collection = db.UnknownContactsLabeled_Round2

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
    idx = st.session_state.current_idx # Unique keys for the UI
    
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
    
    # --- GENDER ---
    gender = st.radio("⚧️ Gender", ["Not sure", "M", "F"], index=0, key=f"gender_{idx}")
        
    st.write("---")
    
    # --- CATEGORY SELECTION (RADIO + OVERRIDE) ---
    category_options = [
        "Don't know", 
        "Client", 
        "DELETE", 
        "Assistant", 
        "B2B", 
        "Service Provider", 
        "Bridal Asia", 
        "Family", 
        "Hotshot", 
        "Business", 
        "Business Owner", 
        "BVRTSE", 
        "IIM", 
        "Instagram", 
        "M&K", 
        "Masterji", 
        "Model", 
        "Procurement", 
        "Stylist", 
        "Waters Edge"
    ]
    
    selected_category = st.radio("📌 Select Category:", category_options, index=0, key=f"cat_radio_{idx}")
    custom_category = st.text_input("✍️ Or type a custom category (overrides radio selection):", key=f"cat_text_{idx}")
    
    st.write("---")

    # --- SERVICE TYPE SELECTION (RADIO + OVERRIDE) ---
    service_options = [
        "None",
        "Event Management", 
        "Food & Beverage", 
        "Production", 
        "Interior", 
        "MUAH", 
        "Artist", 
        "Staff", 
        "Business & Finance", 
        "School Bus",
        "Procurement"
    ]
    selected_service = st.radio("🛠️ Select Service Type:", service_options, index=0, key=f"srv_radio_{idx}")
    custom_service = st.text_input("✍️ Or type a custom service type (overrides radio selection):", key=f"srv_text_{idx}")

    st.write("---")
    
    # --- ADDITIONAL DETAILS ---
    st.markdown("**📝 Organization Details**")
    
    existing_org = str(contact.get('Organization Name', ''))
    if existing_org.lower() == 'nan' or existing_org.lower() == 'no org provided':
        existing_org = ""
        
    new_org_name = st.text_input("🏢 Organization Name", value=existing_org, key=f"org_name_{idx}")
    new_org_title = st.text_input("💼 Organization Title", key=f"org_title_{idx}")

    # --- ACTION LOGIC ---
    if go_back:
        last_contact = df_input.iloc[st.session_state.current_idx - 1]
        collection.delete_one({"Contact_ID": last_contact['Contact_ID']})
        st.session_state.current_idx -= 1
        st.rerun()
        
    if submit_next:
        # Override logic for Category
        final_category = custom_category.strip() if custom_category.strip() != "" else selected_category
        
        # Override logic for Service Type
        final_service = custom_service.strip() if custom_service.strip() != "" else selected_service
        if final_service == "None":
            final_service = "" # Save as blank in DB if 'None' is selected
        
        payload = contact.to_dict()
        payload['Gender'] = gender
        payload['Category'] = final_category
        payload['Service Type'] = final_service
        payload['Organization Name'] = new_org_name.strip()
        payload['Organization Title'] = new_org_title.strip()
        
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
        file_name="final_categorized_contacts_v2.csv",
        mime="text/csv"
    )