"""
preferences_tab.py

This module handles the preferences analysis and visualization functionality for the Vestique wardrobe assistant.
It analyzes user's wardrobe data to determine clothing preferences based on wear patterns.

Dependencies:
- streamlit
- json
- datetime
- decide_preference (from main application)
- initialize_database (from main application)

Note: This module requires access to the main application's initialize_database function
and the decide_preference function to work properly.
"""

import streamlit as st
import json
from datetime import datetime
from decider import decide_preference
def preferences_tab():
    """
    Implements the preferences analysis tab in the Vestique wardrobe assistant.
    Analyzes wardrobe data to determine user preferences and display insights.

    Dependencies:
        - decide_preference function must be imported from the main application
        - initialize_database function must be imported from the main application
        - Requires access to clothing_database.json

    Returns:
        None. Updates Streamlit UI directly.
    """
    try:
        with open('clothing_database.json', 'r') as file:
            data = json.load(file)
            contents = data.get('items', [])

        if not contents:
            st.info("Your wardrobe is empty! Add some items to get personalized insights.")
            return

        # Find items with min and max wear count
        min_view = float('inf')
        max_view = -1
        smallest_des = None
        largest_des = None

        for item in contents:
            wear_count = item.get('wear_count', 0)
            if 'ai_analysis' in item:
                if wear_count < min_view:
                    smallest_des = item['ai_analysis']
                    min_view = wear_count
                if wear_count > max_view:
                    largest_des = item['ai_analysis']
                    max_view = wear_count

        if not smallest_des or not largest_des:
            st.warning("Not enough analyzed items to generate insights.")
            return

        st.markdown(
            """
            <style>
                .spacer { margin-bottom: 20px; }
                .center-header {
                    text-align: center;
                    font-size: 24px;
                    font-weight: bold;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div class='center-header'>👗 Wardrobe Insights and Recommendations</div>", unsafe_allow_html=True)
        st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

        with st.spinner("Analyzing wardrobe preferences..."):
            result = decide_preference(largest_des, smallest_des)
            results_list = json.loads(result)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Traits of Most Worn Items")
            st.markdown("\n".join([f"- {trait}" for trait in results_list[0]]))

        with col2:
            st.markdown("### Traits of Least Worn Items")
            st.markdown("\n".join([f"- {trait}" for trait in results_list[1]]))

        st.markdown("---")
        st.markdown("<div style='text-align: center; font-size: 18px; font-weight: bold;'>Overall Recommendation</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center;'>{results_list[2]}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error analyzing preferences: {str(e)}")
        if st.button("Reset Database"):
            initialize_database()
            st.success("Database reset successfully! Please add new items.")
            st.rerun()