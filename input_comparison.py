import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="Vessel MEShaftPowerActual vs SpeedOG Analysis", layout="wide")

# Title
st.title("🚢 Vessel MEShaftPowerActual vs SpeedOG Analysis")

# Vessel ID to Name mapping
vessel_names = {
    1023: "MH Perseus",
    1005: "PISCES", 
    1007: "CAPELLA*",
    1017: "CETUS",
    1004: "CASSIOPEIA",
    1021: "PYXIS",
    1032: "Cenataurus",
    1016: "CHARA",
    1018: "CARINA*"
}


# Load your dataframe
df = pd.read_csv("combined_output_merged_input_nanremoved.csv")

# Sidebar for filters
st.sidebar.header("🔧 Filters")

# Get unique vessel IDs and create name options
unique_vessel_ids = sorted(df['VesselId'].unique())
vessel_name_options = [vessel_names.get(vid, f"Unknown_{vid}") for vid in unique_vessel_ids]

# Create a mapping for the multiselect (show names, store IDs)
name_to_id = {vessel_names.get(vid, f"Unknown_{vid}"): vid for vid in unique_vessel_ids}

# Multiselect for vessels (showing names)
selected_vessel_names = st.sidebar.multiselect(
    "Select Vessels:",
    options=vessel_name_options,
    default=vessel_name_options[:3],  # Default to first 3 vessels
    help="Choose one or more vessels to display on the plot"
)

# Convert selected names back to IDs
selected_vessel_ids = [name_to_id[name] for name in selected_vessel_names]

# MeanDraft filter
st.sidebar.subheader("🌊 Mean Draft Filter")
min_draft = df['MeanDraft'].min()
max_draft = df['MeanDraft'].max()

col1, col2 = st.sidebar.columns(2)
with col1:
    draft_min = st.number_input(
        "Min Draft:",
        min_value=float(min_draft),
        max_value=float(max_draft),
        value=float(min_draft),
        step=0.5,
        key="draft_min"
    )
with col2:
    draft_max = st.number_input(
        "Max Draft:",
        min_value=float(min_draft),
        max_value=float(max_draft),
        value=float(max_draft),
        step=0.5,
        key="draft_max"
    )

# RelativeWindDirection filter  
st.sidebar.subheader("💨 Relative Wind Direction Filter")
min_wind = df['RelativeWindDirection'].min()
max_wind = df['RelativeWindDirection'].max()

col3, col4 = st.sidebar.columns(2)
with col3:
    wind_min = st.number_input(
        "Min Wind Dir:",
        min_value=float(min_wind),
        max_value=float(max_wind),
        value=float(min_wind),
        step=0.5,
        key="wind_min"
    )
with col4:
    wind_max = st.number_input(
        "Max Wind Dir:",
        min_value=float(min_wind),
        max_value=float(max_wind),
        value=float(max_wind),
        step=0.5,
        key="wind_max"
    )

# Apply all filters to the dataframe (replace the existing filtering section)
if selected_vessel_ids:
    # Filter by vessel IDs
    filtered_df = df[df['VesselId'].isin(selected_vessel_ids)]
    
    # Apply MeanDraft filter
    filtered_df = filtered_df[
        (filtered_df['MeanDraft'] >= draft_min) & 
        (filtered_df['MeanDraft'] <= draft_max)
    ]
    
    # Apply RelativeWindDirection filter
    filtered_df = filtered_df[
        (filtered_df['RelativeWindDirection'] >= wind_min) & 
        (filtered_df['RelativeWindDirection'] <= wind_max)
    ]

    
    # Add vessel names to the dataframe for display
    filtered_df = filtered_df.copy()
    filtered_df['vessel_name'] = filtered_df['VesselId'].map(vessel_names)
    

    
    

    import plotly.graph_objects as go
    import numpy as np
    import plotly.express as px

    # One palette for scatter points, another for trendlines
    scatter_palette = px.colors.qualitative.Set3        # For points
    trendline_palette = px.colors.qualitative.Plotly    # For lines (high contrast vs Set3)

    fig = go.Figure()

    for i, vessel_id in enumerate(selected_vessel_ids):
        vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
        vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
        scatter_color = scatter_palette[i % len(scatter_palette)]
        fig.add_trace(go.Scatter(
            x=vessel_data['SpeedOG'],
            y=vessel_data['MEShaftPowerActual'],
            mode='markers',
            name=vessel_name,
            legendgroup=vessel_name,
            marker=dict(color=scatter_color, size=7, opacity=0.60),
            showlegend=True,
            customdata=np.stack((vessel_data['SpeedOG'], vessel_data['MEShaftPowerActual'], vessel_data['VesselId']), axis=-1),
            hovertemplate=(
                f"Vessel: {vessel_name}<br>"
                # "Vessel ID: %{customdata[2]}<br>"
                "SpeedOG: %{customdata[0]:.2f} knots<br>"
                "MEShaftPowerActual: %{customdata[1]:.2f} kW<br>"
                "<extra></extra>"
            ),
        ))

    # 2. Trendlines (contrasting color, visually distinct)
    for i, vessel_id in enumerate(selected_vessel_ids):
        vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
        vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
        trend_color = trendline_palette[i % len(trendline_palette)]
        if len(vessel_data) > 3:
            vessel_data_sorted = vessel_data.sort_values('SpeedOG')
            coeffs = np.polyfit(vessel_data_sorted['SpeedOG'], vessel_data_sorted['MEShaftPowerActual'], 3)
            poly_func = np.poly1d(coeffs)
            x_smooth = np.linspace(vessel_data_sorted['SpeedOG'].min(), vessel_data_sorted['SpeedOG'].max(), 100)
            y_smooth = poly_func(x_smooth)
            fig.add_trace(go.Scatter(
                x=x_smooth,
                y=y_smooth,
                mode='lines',
                name=f'{vessel_name} (Trend)',
                line=dict(color=trend_color, width=4, dash='solid'),
                legendgroup=vessel_name,
                showlegend=True
            ))

    fig.update_layout(
        title="MEShaftPowerActual vs SpeedOG by Vessel with Polynomial Trends (Contrast Colors)",
        xaxis_title='SpeedOG (knots)',
        yaxis_title='MEShaftPowerActual (kW)',
        width=900,
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        margin=dict(r=150)
    )

    st.plotly_chart(fig, use_container_width=True)
    
#     # Display summary statistics
#     st.subheader("📊 Summary Statistics")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.write("**Selected Vessels:**")
#         for vessel_id in selected_vessel_ids:
#             vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
#             vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
#             st.write(f"• {vessel_name} (ID: {vessel_id}): {len(vessel_data)} data points")
    
#     with col2:
#         st.write("**Overall Statistics:**")
#         st.write(f"• Total data points: {len(filtered_df)}")
#         st.write(f"• SpeedOG range: {filtered_df['SpeedOG'].min():.1f} - {filtered_df['SpeedOG'].max():.1f} knots")
#         st.write(f"• MEShaftPowerActual range: {filtered_df['MEShaftPowerActual'].min():.0f} - {filtered_df['MEShaftPowerActual'].max():.0f} kW")
    
#     # # Optional: Display raw data
#     # with st.expander("📋 View Raw Data"):
#     #     st.dataframe(filtered_df)

# else:
#     st.warning("⚠️ Please select at least one vessel from the sidebar to display the plot.")
    


