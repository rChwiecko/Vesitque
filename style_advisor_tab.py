# import streamlit as st
# import json
# from style_advisor import StyleAdvisor

# def style_advisor_tab(tracker):
#     # Add custom styling with proper padding and dark theme
#     st.markdown("""
#         <style>
#             /* Container styling */
#             .main-container {
#                 background-color: #1E1E1E;
#                 padding: 20px;
#                 border-radius: 12px;
#                 margin: 10px 0;
#             }
            
#             /* Image and content grid */
#             .grid-container {
#                 display: grid;
#                 grid-template-columns: 1fr 2fr;
#                 gap: 20px;
#                 margin: 20px 0;
#             }
            
#             /* Image card */
#             .image-card {
#                 background-color: #2D2D2D;
#                 border-radius: 12px;
#                 padding: 16px;
#                 text-align: center;
#             }
            
#             /* Advice container */
#             .advice-container {
#                 background-color: #2D2D2D;
#                 border-radius: 12px;
#                 padding: 24px;
#                 margin-top: 10px;
#             }
            
#             /* Typography */
#             .item-title {
#                 color: #E0E0E0;
#                 font-size: 1.2rem;
#                 margin: 12px 0;
#                 text-align: center;
#             }
            
#             .advice-text {
#                 color: #CCCCCC;
#                 line-height: 1.6;
#                 font-size: 1rem;
#             }
            
#             /* Sources section */
#             .sources {
#                 margin-top: 20px;
#                 padding-top: 16px;
#                 border-top: 1px solid #3D3D3D;
#                 color: #888888;
#                 font-size: 0.9rem;
#             }
#         </style>
#     """, unsafe_allow_html=True)
    
#     st.subheader("👔 Style Advisor")
    
#     if 'style_advisor' not in st.session_state:
#         st.session_state.style_advisor = StyleAdvisor('ba4070a0-299d-4e64-8952-0886808164b3')
    
#     if tracker.database["items"]:
#         selected_item = st.selectbox(
#             "Select an item for styling advice",
#             options=tracker.database["items"],
#             format_func=lambda x: x.get('name', x['type'])
#         )
        
#         if selected_item:
#             try:
#                 # Debug output
#                 if st.session_state.get('debug_mode', False):
#                     st.write("Selected item:", selected_item)
                
#                 # Get the AI analysis
#                 ai_analysis = selected_item.get('ai_analysis')
#                 if not ai_analysis:
#                     st.warning("This item doesn't have AI analysis data.")
#                     return

#                 # Parse the AI analysis and extract item type
#                 try:
#                     if isinstance(ai_analysis, str) and '```json' in ai_analysis:
#                         # Extract JSON between markdown code blocks
#                         json_content = ai_analysis.split('```json\n')[1].split('\n```')[0]
#                         ai_data = json.loads(json_content)
#                     elif isinstance(ai_analysis, str):
#                         # Use the raw string if no markdown
#                         ai_data = json.loads(ai_analysis)
#                     else:
#                         # If it's already a dict, use it directly
#                         ai_data = ai_analysis

#                     # Use the more specific type from AI analysis if available
#                     item_type = ai_data.get('type') or selected_item.get('type', 'Unknown')

#                     # Combine with item metadata
#                     item_description = {
#                         'name': selected_item.get('name', 'Unknown'),
#                         'type': item_type,  # Use the more specific type from AI analysis
#                         'brand': selected_item.get('brand', ai_data.get('brand', 'Unknown')),
#                         'color': ai_data.get('color', {}),
#                         'fit_and_style': ai_data.get('fit_and_style', {}),
#                         'material': ai_data.get('material', 'Unknown'),
#                         'design_features': ai_data.get('design_features', {}),
#                         'condition': ai_data.get('condition', 'Unknown'),
#                         'season': ai_data.get('season', 'Unknown'),
#                         'use_case': ai_data.get('use_case', [])
#                     }

#                     # Create display grid
#                     col1, col2 = st.columns([1, 2])

#                     with col1:
#                         if 'image' in selected_item:
#                             image = tracker.base64_to_image(selected_item['image'])
#                             if image:
#                                 st.image(image, use_column_width=True)
                        
#                         st.markdown(f"### Item Details")
#                         st.markdown(f"**Type:** {item_type}")
#                         st.markdown(f"**Material:** {item_description['material']}")
#                         if 'design_features' in ai_data:
#                             st.markdown("**Features:**")
#                             for key, value in ai_data['design_features'].items():
#                                 if isinstance(value, list):
#                                     st.markdown(f"- {key}: {', '.join(value)}")
#                                 else:
#                                     st.markdown(f"- {key}: {value}")

#                     with col2:
#                         with st.spinner("Getting style advice..."):
#                             # Get style advice using the enhanced item description
#                             advice = st.session_state.style_advisor.get_style_advice(item_description)
                            
#                             # Display advice
#                             st.markdown("### Styling Tips")
#                             st.markdown(advice["styling_tips"])
                            
#                             # Display sources
#                             with st.expander("Sources"):
#                                 for source in advice["sources"]:
#                                     st.caption(f"- {source}")

#                 except json.JSONDecodeError as e:
#                     st.error(f"Error parsing AI analysis data: {e}")
#                 except Exception as e:
#                     st.error(f"Error processing item data: {e}")

#             except Exception as e:
#                 st.error(f"Error in style advisor: {e}")
#     else:
#         st.info("Add some items to your wardrobe to get personalized style advice!")