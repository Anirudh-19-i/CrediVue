import streamlit as st
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore
import datetime
import google.auth
import pandas as pd
import plotly.express as px
import hashlib

# --- SETUP & CONFIG ---
st.set_page_config(page_title="CrediVue AI", page_icon="🧭", layout="wide")
# NOTE: Credentials automatically picked up in Cloud Run environment
credentials, PROJECT_ID = google.auth.default()
LOCATION = "us-central1"

# Initialize Google Services
# The project ID is usually inferred from the environment
db = firestore.Client(project=PROJECT_ID)
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.5-flash")

# --- UTILITIES ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- AUTHENTICATION FUNCTIONS ---

def register_user(username, password):
    users_ref = db.collection("users")
    if users_ref.document(username).get().exists:
        st.error("Username already exists. Please choose a different one.")
        return False
    
    hashed_password = hash_password(password)
    users_ref.document(username).set({
        "password": hashed_password,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    st.success("Account created successfully! Please log in.")
    return True

def check_login(username, password):
    users_ref = db.collection("users")
    doc = users_ref.document(username).get()
    
    if doc.exists:
        stored_hash = doc.to_dict().get("password")
        if stored_hash == hash_password(password):
            return True
    return False

def login_page():
    st.markdown("""
        <style>
        .big-font { font-size:50px !important; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 20px;}
        .subheader-style { text-align: center; margin-bottom: 40px;}
        </style>
        <p class="big-font">CrediVue AI 🧭</p>
        <p class="subheader-style">Your Clear Path to Financial Clarity.</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    action = st.radio("Choose Action", ["Login", "Sign Up"], horizontal=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        username = st.text_input("Username (Must be unique)")
        password = st.text_input("Password", type="password")
        
        if action == "Login":
            if st.button("Log In"):
                if check_login(username, password):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
                    
        elif action == "Sign Up":
            if st.button("Sign Up"):
                if username and password:
                    register_user(username, password)
                else:
                    st.error("Please enter both username and password.")

# --- DEDICATED STUDENT PAGE (CAMPUS $ENSE$) ---

# CALLBACK FUNCTION for interactive buttons
def set_student_query(query):
    """Sets the value of the text area widget directly using its session state key."""
    st.session_state['student_qa_input'] = query

def page_campus_sense():
    st.title("👨‍🎓 Campus $ense$: Financial Literacy for Students")
    st.markdown("#### Learn smart money habits through interactive, Indian-focused scenarios.")
    st.warning("💡 **Tip:** Use the Q&A section below to test scenarios related to your student life, CIBIL, or first investments.")
    st.markdown("---")
    
    # Predefined Scenarios / Learning Paths
    st.subheader("Quick Learning Scenarios")
    
    col_scen1, col_scen2, col_scen3 = st.columns(3)
    
    with col_scen1:
        st.button("Budgeting Basics Challenge", 
                  on_click=set_student_query, 
                  args=("I have ₹12,000 pocket money for the month. How should I allocate it among food, transport, books, and entertainment to save 20%?",))
    
    with col_scen2:
        st.button("Building CIBIL Score Challenge",
                  on_click=set_student_query,
                  args=("I am 18 and want a good credit score before I graduate. What is the single best action I should take now?",))
            
    with col_scen3:
        st.button("Loan vs. EMI Challenge",
                  on_click=set_student_query,
                  args=("I need to buy a new laptop costing ₹80,000. Should I use a BNPL (Buy Now Pay Later) option or ask my parents for a small personal loan? Compare the risks.",))
            
    st.markdown("---")
    
    # Interactive Q&A Session
    st.subheader("Ask Your Own Money Question")
    
    # Initialize the key for the text area if it doesn't exist
    if 'student_qa_input' not in st.session_state:
        st.session_state['student_qa_input'] = "Ask a question about student finances..."
        
    # The text area's initial/current value is always read from the session state key
    custom_query = st.text_area(
        "Your Scenario:", 
        value=st.session_state['student_qa_input'], 
        key='student_qa_input',
        height=100
    )

    if st.button("Get AI Financial Coaching"):
        if custom_query and custom_query != "Ask a question about student finances...":
            with st.spinner("Analyzing scenario and drafting your lesson..."):
                prompt = f"""
                Act as a highly engaging and non-judgemental financial tutor named 'CrediTutor' specifically for Indian university students. 
                Your goal is to be educational and practical.
                
                Student Question: "{custom_query}"
                
                Provide a structured, easy-to-read answer focusing on:
                1. **Lesson Goal:** What is the main principle being taught?
                2. **The CrediTutor Solution:** A step-by-step practical guide.
                3. **Indian Reality Check:** Mention relevant Indian terms like CIBIL, SIP, or specific banking habits.
                """
                response = model.generate_content(prompt).text
                st.markdown("### 📚 Your CrediTutor Lesson:")
                st.markdown(response)
                
                # Clear the text area after submission
                st.session_state['student_qa_input'] = "Ask a question about student finances..."
                st.rerun() # Force a rerun to clear the text area

        else:
            st.error("Please enter a valid question.")


# --- CARD MANAGEMENT FUNCTIONS ---

def add_credit_card_form():
    st.subheader("➕ Add New Credit Card")
    with st.form("add_card_form", clear_on_submit=True):
        card_name = st.text_input("Card Name (e.g., HDFC Millennia)")
        card_limit = st.number_input("Credit Limit (₹)", min_value=10000, step=5000)
        card_features = st.text_area("Key Features (e.g., 5% cashback on Amazon)")
        
        submitted = st.form_submit_button("Save Card")
        if submitted and card_name:
            card_data = {
                "name": card_name,
                "limit": card_limit,
                "features": card_features,
                "added_at": firestore.SERVER_TIMESTAMP,
                # Mock transaction data for demo purposes
                "transactions": [
                    {"date": datetime.datetime.now(), "amount": 2500, "category": "Dining"},
                    {"date": datetime.datetime.now() - datetime.timedelta(days=5), "amount": 7500, "category": "Online Shopping"},
                ],
                "current_spend": 10000 
            }
            db.collection("users").document(st.session_state['username']).collection("cards").add(card_data)
            st.success(f"Card '{card_name}' added successfully!")

def page_manage_cards():
    st.title("💳 Manage My Cards")
    add_credit_card_form()
    st.markdown("---")
    st.subheader("Your Credit Card Portfolio")
    
    cards_ref = db.collection("users").document(st.session_state['username']).collection("cards").stream()
    
    card_count = 0
    for card_doc in cards_ref:
        card_count += 1
        card = card_doc.to_dict()
        
        if card['limit'] > 0:
            utilization = (card['current_spend'] / card['limit']) * 100
        else:
            utilization = 0
        
        with st.expander(f"**{card['name']}** (Limit: ₹{card['limit']:,}) - Utilization: {utilization:.1f}%", expanded=True):
            col_feat, col_hist = st.columns([1, 1])
            
            formatted_features = card['features'].replace('\n', '\n- ')
            
            with col_feat:
                st.markdown("#### Card Features & Insights")
                st.info(f"**Limit:** ₹{card['limit']:,}")
                st.warning(f"**Current Spend:** ₹{card['current_spend']:,}")
                st.markdown(f"**Key Features:**\n- {formatted_features}") 
                st.markdown("---")
                st.markdown("#### Card-Specific Offer")
                if "cashback" in card['name'].lower() or "millennia" in card['name'].lower():
                     st.success("✅ **AI Suggestion:** Use this card for all major online spending this month to trigger the bonus cashback tier.")
                else:
                    st.info("💡 **AI Suggestion:** Look for Travel partners to maximize the value of this card's points system.")


            with col_hist:
                st.markdown("#### Transaction History (Mock Data)")
                transactions_df = pd.DataFrame(card['transactions'])
                transactions_df['date'] = transactions_df['date'].apply(lambda x: x.strftime('%d-%b'))
                st.dataframe(transactions_df[['date', 'category', 'amount']].rename(columns={'amount': 'Amount (₹)'}))
                
                st.markdown("#### Credit Health Meter")
                if utilization < 30:
                    st.success(f"✅ Low Utilization: {utilization:.1f}%")
                else:
                    st.error(f"❌ High Utilization: {utilization:.1f}% (Pay down now!)")

    if card_count == 0:
        st.info("No cards found. Please add your first card above!")

# --- ADVISOR PAGE ---

def page_advisor():
    st.header("🤖 AI Credit Advisor")
    
    col1, col2 = st.columns(2)
    with col1:
        income = st.number_input("Monthly Income (₹)", 15000)
        score = st.number_input("CIBIL Score", 0, 900, 750)
    with col2:
        debt = st.number_input("Current Card Debt (₹)", 0, value=5000)
        goal = st.selectbox("Financial Goal", ["Increase Score", "Get Premium Card", "Clear Debt", "Student Loan"])

    query = st.text_area("Ask a specific question:", "I want to apply for HDFC Millennia. Do I qualify?")
    
    if st.button("Analyze with Gemini"):
        with st.spinner("Consulting experts..."):
            prompt = f"""
            Act as CrediVue AI, a specialized financial advisor for the Indian market focused on foresight.
            User: {st.session_state['username']}, Income: ₹{income}, CIBIL: {score}, Debt: ₹{debt}, Goal: {goal}.
            Question: {query}
            
            Output format:
            1. **Vue Verdict**: Safe to proceed or Risky? (The 'Vue' is your forward-looking assessment).
            2. **Strategy**: 3 clear steps to reach the goal.
            3. **Context**: Mention specific Indian banks/rules (RBI, CIBIL).
            """
            response = model.generate_content(prompt).text
            st.markdown(response)
            
            # Save to History
            db.collection("users").document(st.session_state['username']).collection("history").add({
                "query": query,
                "response": response,
                "timestamp": firestore.SERVER_TIMESTAMP
            })

def page_history():
    st.header("📜 Consultation History")
    docs = db.collection("users").document(st.session_state['username']).collection("history").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    
    found = False
    for doc in docs:
        found = True
        d = doc.to_dict()
        with st.expander(f"Query: {d.get('query', 'No Query')} ({d.get('timestamp', datetime.datetime.now()).strftime('%d-%b')})"):
            st.markdown(d.get('response'))
            
    if not found:
        st.info("No history found. Go to 'Advisor' to ask your first question!")

def page_spend_analysis():
    st.header("📊 Spend Analysis & Insights")
    
    st.markdown("### 💳 Active Cards & Spending")
    
    # Mock Data for the Demo
    data = {
        'Category': ['Dining', 'Travel', 'UPI (Small Merchant)', 'Shopping', 'Fuel'],
        'Amount': [4500, 2000, 1500, 8000, 3000]
    }
    df = pd.DataFrame(data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(df, values='Amount', names='Category', title='Spending Breakdown (This Month)', hole=0.4)
        st.plotly_chart(fig)
        
    with col2:
        st.success("💡 **CrediVue Insight:** Your 'Shopping' spend is 42% of your total. Utilize the **SBI Cashback Card** for online purchases to maximize rewards and save roughly ₹400/month.")
        st.warning("⚠️ **Utilization Alert:** You have used 45% of your limit. Paying down ₹5,000 immediately is crucial to improve your CIBIL score quickly.")

def page_offers():
    st.header("🎁 Curated Offers for You")
    
    offers = [
        {"card": "IDFC First WOW", "type": "Secured (FD)", "benefit": "No CIBIL Required. 6.5% Interest on FD.", "url": "https://www.idfcfirstbank.com/credit-card/first-wow"},
        {"card": "SBI Cashback", "type": "Shopping", "benefit": "5% Flat Cashback on Online Spends.", "url": "https://www.sbicard.com/en/personal/credit-cards/cashback-credit-card.page"},
        {"card": "HDFC Millennia", "type": "All Rounder", "benefit": "5% Cashback on Amazon/Flipkart + Free Lounge.", "url": "https://www.hdfcbank.com/personal/pay/cards/credit-cards/millennia-credit-card"},
        {"card": "Axis Ace", "type": "Utility Bills", "benefit": "5% Cashback on GPay Bill Payments.", "url": "https://www.axisbank.com/retail/cards/credit-card/axis-ace-credit-card"}
    ]
    
    for offer in offers:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(offer["card"])
                st.caption(f"Best for: {offer['type']}")
                st.write(offer["benefit"])
            with c2:
                st.markdown(f"**[Apply Now >>]({offer['url']})**", unsafe_allow_html=True)

# --- MAIN CONTROL FLOW ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None

if not st.session_state['authenticated']:
    login_page()
else:
    # Sidebar Navigation
    st.sidebar.title(f"👤 {st.session_state['username']}")
    page = st.sidebar.radio("Navigate", ["Advisor", "Campus Sense", "Manage Cards", "Spend Analysis", "My History", "Offers"])
    
    if st.button("Logout", key="logout_btn"):
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.info("Powered by Google Gemini 2.5 & Cloud Run")

    # Route to pages
    if page == "Advisor":
        page_advisor()
    elif page == "Campus Sense":
        page_campus_sense()
    elif page == "Manage Cards":
        page_manage_cards()
    elif page == "Spend Analysis":
        page_spend_analysis()
    elif page == "My History":
        page_history()
    elif page == "Offers":
        page_offers()
