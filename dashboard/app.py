import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="AppWeave Dashboard",
    page_icon="📱",
    layout="wide"
)

def get_connection():
    try:
        db_url = st.secrets["DATABASE_URL"]
    except:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        db_url = os.getenv('DATABASE_URL')
    return psycopg2.connect(db_url)

def get_all_apps():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT m.package_name, m.app_name, m.category,
               m.rating, m.installs, m.developer_name,
               c.gender_label, c.signal_tier,
               c.age_primary, c.income_label,
               c.gender_score, c.gender_reasoning
        FROM app_metadata m
        JOIN app_classifications c ON m.package_name = c.package_name
        WHERE m.country='in'
        ORDER BY m.rating_count DESC NULLS LAST
    """, conn)
    conn.close()
    return df

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM app_classifications WHERE country='in'")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT signal_tier, COUNT(*) FROM app_classifications WHERE country='in' GROUP BY signal_tier")
    tiers = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT gender_label, COUNT(*) FROM app_classifications WHERE country='in' GROUP BY gender_label")
    genders = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT m.category, COUNT(*)
        FROM app_metadata m
        JOIN app_classifications c ON m.package_name = c.package_name
        WHERE m.country='in'
        GROUP BY m.category
        ORDER BY COUNT(*) DESC
    """)
    categories = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.close()
    conn.close()
    return {
        "total_classified": total,
        "tier_distribution": tiers,
        "gender_distribution": genders,
        "category_distribution": categories
    }

st.sidebar.title("AppWeave")
st.sidebar.markdown("Demographic Intelligence for Mobile Apps")
page = st.sidebar.selectbox(
    "Navigate",
    ["App Browser", "App Detail", "Stats", "Review Queue"]
)

if page == "App Browser":
    st.title("App Browser")
    col1, col2, col3, col4 = st.columns(4)
    gender_filter = col1.selectbox("Gender", ["All", "female", "male", "neutral"])
    tier_filter = col2.selectbox("Signal Tier", ["All", "S", "A", "B", "C"])
    category_filter = col3.selectbox("Category", ["All", "Shopping", "Finance", "Health & Fitness", "Food & Drink", "Social", "Communication"])
    search = col4.text_input("Search app name")

    df = get_all_apps()

    if gender_filter != "All":
        df = df[df['gender_label'] == gender_filter]
    if tier_filter != "All":
        df = df[df['signal_tier'] == tier_filter]
    if category_filter != "All":
        df = df[df['category'] == category_filter]
    if search:
        df = df[df['app_name'].str.contains(search, case=False, na=False)]

    st.markdown(f"**{len(df)} apps found**")
    st.dataframe(
        df[['app_name','category','gender_label','signal_tier','age_primary','income_label','rating','installs']].rename(columns={
            'app_name':'App Name','category':'Category','gender_label':'Gender',
            'signal_tier':'Tier','age_primary':'Age Group','income_label':'Income',
            'rating':'Rating','installs':'Installs'
        }),
        use_container_width=True,
        height=500
    )

elif page == "App Detail":
    st.title("App Detail")
    df = get_all_apps()
    selected = st.selectbox("Select an app", df['app_name'].tolist())
    if selected:
        app = df[df['app_name'] == selected].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("App Info")
            st.write(f"**Package:** {app['package_name']}")
            st.write(f"**Category:** {app['category']}")
            st.write(f"**Rating:** {app['rating']:.1f}")
            st.write(f"**Installs:** {app['installs']}")
            st.write(f"**Developer:** {app['developer_name']}")
        with col2:
            st.subheader("Demographic Profile")
            tier_colors = {'S':'🟢','A':'🔵','B':'🟡','C':'⚪'}
            st.write(f"**Signal Tier:** {tier_colors.get(app['signal_tier'],'')} {app['signal_tier']}")
            st.write(f"**Gender:** {app['gender_label'].upper()}")
            st.write(f"**Gender Score:** {app['gender_score']:.2f}")
            st.write(f"**Age Group:** {app['age_primary']}")
            st.write(f"**Income:** {app['income_label'].upper()}")
        st.subheader("AI Reasoning")
        st.info(app['gender_reasoning'])
        st.subheader("Override Classification")
        col3, col4, col5 = st.columns(3)
        new_gender = col3.selectbox("New Gender", ["female", "male", "neutral"])
        new_tier = col4.selectbox("New Tier", ["S", "A", "B", "C"])
        if col5.button("Save Override"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE app_classifications
                SET gender_label=%s, signal_tier=%s
                WHERE package_name=%s AND country='in'
            """, (new_gender, new_tier, app['package_name']))
            conn.commit()
            cursor.close()
            conn.close()
            st.success("Override saved!")

elif page == "Stats":
    st.title("Statistics")
    stats = get_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Apps Classified", stats['total_classified'])
    col2.metric("Categories", len(stats['category_distribution']))
    col3.metric("Strong Signal Apps",
        stats['tier_distribution'].get('S', 0) +
        stats['tier_distribution'].get('A', 0)
    )

    col4, col5 = st.columns(2)
    with col4:
        st.subheader("Signal Tier Distribution")
        tier_df = pd.DataFrame(
            list(stats['tier_distribution'].items()),
            columns=['Tier', 'Count']
        )
        fig = px.pie(tier_df, values='Count', names='Tier')
        st.plotly_chart(fig, use_container_width=True)

    with col5:
        st.subheader("Gender Distribution")
        gender_df = pd.DataFrame(
            list(stats['gender_distribution'].items()),
            columns=['Gender', 'Count']
        )
        fig2 = px.bar(gender_df, x='Gender', y='Count', color='Gender',
            color_discrete_map={'female':'#FF69B4','male':'#4169E1','neutral':'#808080'})
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Apps by Category")
    cat_df = pd.DataFrame(
        list(stats['category_distribution'].items()),
        columns=['Category', 'Count']
    )
    fig3 = px.bar(cat_df, x='Category', y='Count', color='Count',
        color_continuous_scale='Blues')
    st.plotly_chart(fig3, use_container_width=True)

elif page == "Review Queue":
    st.title("Review Queue")
    conn = get_connection()
    df = pd.read_sql("""
        SELECT m.app_name, m.package_name, m.installs,
               c.gender_label, c.signal_tier,
               c.gender_confidence, c.age_confidence
        FROM app_metadata m
        JOIN app_classifications c ON m.package_name = c.package_name
        WHERE m.country='in'
        AND (c.gender_confidence='low' OR c.age_confidence='low')
        ORDER BY m.rating_count DESC NULLS LAST
    """, conn)
    conn.close()
    if len(df) == 0:
        st.success("No apps need review!")
    else:
        st.warning(f"{len(df)} apps need manual review")
        st.dataframe(df, use_container_width=True)