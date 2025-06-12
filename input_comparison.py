import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import math

# Page configuration
st.set_page_config(page_title="Vessel MEShaftPowerActual vs Speed Analysis", layout="wide")

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

df = df[(df["IsSpeedDropValid"]==1) & (df["IsDeltaPDOnSpeedValid"]==1)]

df["LCVCorrectedFOC"] = df["ISOCorrectedFOC"] +df["MEFOCIdealPD"] - df["MEFOCIdealPDCor"]

# Sidebar for filters
st.sidebar.header("🔧 Filters")

# Speed Type Selection - Add this at the top of sidebar
st.sidebar.subheader("🚤 Speed Type Selection")
speed_type = st.sidebar.radio(
    "Select Speed Type:",
    options=["SpeedOG", "SpeedTW"],
    index=0,  # Default to SpeedOG (index 0)
    help="Choose between Speed Over Ground (SpeedOG) or Speed Through Water (SpeedTW)"
)

# Update title based on selection
st.title(f"🚢 MEShaftPowerActual vs {speed_type} Analysis")

# Get the selected speed column
speed_column = speed_type

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

# Dynamic Speed Filter based on selected speed type
st.sidebar.subheader(f"🚤 {speed_type} Filter")
min_speed = df[speed_column].min()
max_speed = df[speed_column].max()

col3, col4 = st.sidebar.columns(2)
with col3:
    speed_min = st.number_input(
        f"Min {speed_type}:",
        min_value=float(min_speed),
        max_value=float(max_speed),
        value=float(min_speed),
        step=0.5,
        key=f"{speed_type.lower()}_min"
    )
with col4:
    speed_max = st.number_input(
        f"Max {speed_type}:",
        min_value=float(min_speed),
        max_value=float(max_speed),
        value=float(max_speed),
        step=0.5,
        key=f"{speed_type.lower()}_max"
    )

st.sidebar.subheader("💨 Beaufort Scale Filter")
min_bf = df['BFScale'].min()
max_bf = df['BFScale'].max()

col3, col4 = st.sidebar.columns(2)
with col3:
    bf_min = st.number_input(
        "Min BF Scale:",
        min_value=float(min_bf),
        max_value=float(max_bf),
        value=float(min_bf),
        step=0.5,
        key="bf_min"
    )
with col4:
    bf_max = st.number_input(
        "Max BF Scale:",
        min_value=float(min_bf),
        max_value=float(max_bf),
        value=float(max_bf),
        step=0.5,
        key="bf_max"
    )

# Apply all filters to the dataframe
if selected_vessel_ids:
    # Filter by vessel IDs
    filtered_df = df[df['VesselId'].isin(selected_vessel_ids)]
    
    filtered_df = filtered_df[
        (filtered_df['MeanDraft'] >= draft_min) & 
        (filtered_df['MeanDraft'] <= draft_max) & 
        (filtered_df['RelativeWindDirection'] >= wind_min) & 
        (filtered_df['RelativeWindDirection'] <= wind_max)& 
        (filtered_df[speed_column] >= speed_min) &
        (filtered_df[speed_column] <= speed_max)&
        (filtered_df['BFScale'] >= bf_min) &
        (filtered_df['BFScale'] <= bf_max)
    ]
    
    # Add vessel names to the dataframe for display
    filtered_df = filtered_df.copy()
    filtered_df['vessel_name'] = filtered_df['VesselId'].map(vessel_names)

    # OPTIMIZED COLOR PALETTE FOR 8 VESSELS (16 colors) + 2 EXTRA
    # These colors are hand-picked and tested for maximum visual distinction

    # Scatter point colors - High contrast, easily distinguishable
    scatter_colors = [
        "#E85252",  # Bright Red
        "#6868CF",  # Bright Blue  
        "#A8ECA8",  # Bright Green
        "#F8B15F",  # Orange
        "#D3ACEE",  # Purple
        "#84EDED",  # Cyan
        "#F392C6",  # Hot Pink
        "#E6E97B",  # Lime Green
    ]

    # Trendline colors - Darker, contrasting versions with different hues
    trendline_colors = [
        "#E70E0E",  # Bright Red
        "#2B2BD0",  # Bright Blue  
        "#6BEC6B",  # Bright Green
        "#FA8C0F",  # Orange
        "#BA71EF",  # Purple
        '#00FFFF',  # Cyan
        "#F8349C",  # Hot Pink
        "#ECF406",  # Lime Green
    ]

    # Verify we have enough colors
    n_vessels = len(selected_vessel_ids)
    if n_vessels > len(scatter_colors):
        st.error(f"Not enough predefined colors! Need {n_vessels}, have {len(scatter_colors)}")
        st.stop()

    fig = go.Figure()

    # 1. Add scatter points with predefined distinct colors
    for i, vessel_id in enumerate(selected_vessel_ids):
        vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
        vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
        
        fig.add_trace(go.Scatter(
            x=vessel_data[speed_column],
            y=vessel_data['MEShaftPowerActual'],
            mode='markers',
            name=vessel_name,
            legendgroup=vessel_name,
            marker=dict(
                color=scatter_colors[i], 
                size=8,  # Slightly larger for better visibility
                opacity=0.70,  # Increased opacity for better distinction
                line=dict(width=1.5, color='white')  # Thicker white border
            ),
            showlegend=True,
            customdata=np.stack((vessel_data[speed_column], vessel_data['MEShaftPowerActual'], vessel_data['VesselId']), axis=-1),
            hovertemplate=(
                f"<b>Vessel: {vessel_name}</b><br>"
                f"{speed_type}: %{{customdata[0]:.2f}} knots<br>"
                "MEShaftPowerActual: %{customdata[1]:.2f} kW<br>"
                "<extra></extra>"
            ),
        ))

    # 2. Add trendlines with contrasting predefined colors
    for i, vessel_id in enumerate(selected_vessel_ids):
        vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
        vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
        
        if len(vessel_data) > 3:
            vessel_data_sorted = vessel_data.sort_values(speed_column)
            coeffs = np.polyfit(vessel_data_sorted[speed_column], vessel_data_sorted['MEShaftPowerActual'], 3)
            poly_func = np.poly1d(coeffs)
            x_smooth = np.linspace(vessel_data_sorted[speed_column].min(), vessel_data_sorted[speed_column].max(), 100)
            y_smooth = poly_func(x_smooth)
            
            fig.add_trace(go.Scatter(
                x=x_smooth,
                y=y_smooth,
                mode='lines',
                name=f'{vessel_name} (Trend)',
                line=dict(
                    color=trendline_colors[i], 
                    width=4,  # Thick lines for better visibility
                    dash='solid'
                ),
                legendgroup=vessel_name,
                showlegend=True,
                hoverinfo='skip'
            ))

    # Enhanced layout for better color distinction
    fig.update_layout(
        xaxis_title=f'{speed_type} (knots)',
        yaxis_title='MEShaftPowerActual (kW)',
        width=900,
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255, 255, 255, 0.9)",  # Semi-transparent white background
            bordercolor="gray",
            borderwidth=1
        ),
        margin=dict(r=180),  # More space for legend
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Subtle grid for better readability without interfering with colors
    fig.update_xaxes(
        gridcolor='rgba(128, 128, 128, 0.2)',
        gridwidth=1,
        griddash='dot',
        zeroline=True,
        zerolinecolor='rgba(128, 128, 128, 0.4)',
        zerolinewidth=1
    )
    fig.update_yaxes(
        gridcolor='rgba(128, 128, 128, 0.2)',
        gridwidth=1,
        griddash='dot',
        zeroline=True,
        zerolinecolor='rgba(128, 128, 128, 0.4)',
        zerolinewidth=1
    )

    st.plotly_chart(fig, use_container_width=True)

    # Create Summary Tables for Speed Ranges
    st.subheader(f"📊 {speed_type} Range Analysis")
    
    # Define speed ranges with step of 1
    min_speed_range = math.floor(filtered_df[speed_column].min())
    max_speed_range = math.ceil(filtered_df[speed_column].max())
    speed_ranges = [(i, i+1) for i in range(min_speed_range, max_speed_range)]
    
    for speed_min_range, speed_max_range in speed_ranges:
        # Filter data for this speed range
        speed_range_df = filtered_df[
            (filtered_df[speed_column] >= speed_min_range) & 
            (filtered_df[speed_column] < speed_max_range)
        ]
        
        if len(speed_range_df) > 0:  # Only show ranges that have data
            st.write(f"\n### {speed_type} in {speed_min_range}-{speed_max_range} knots")
            
            summary_data = []
            
            for vessel_id in selected_vessel_ids:
                vessel_data = speed_range_df[speed_range_df['VesselId'] == vessel_id]
                vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
                
                if len(vessel_data) > 0:
                    # Calculate weighted averages using ME1RunningHoursMinute as weights
                    total_running_hours_min = vessel_data['ME1RunningHoursMinute'].sum()
                    
                    if total_running_hours_min > 0:
                        # Weighted average for MEShaftPowerActual
                        weighted_avg_power = (vessel_data['MEShaftPowerActual'] * 
                            vessel_data['ME1RunningHoursMinute']).sum() / total_running_hours_min
                        
                        # Calculate LCVCorrectedFOC per day
                        total_fuel_consumed = vessel_data['LCVCorrectedFOC'].sum()
                        fuel_consumption_mt_per_minute = total_fuel_consumed / total_running_hours_min
                        fuel_consumption_mt_per_day = fuel_consumption_mt_per_minute * 1440
                        
                        # Add to summary data
                        summary_data.append({
                            'Vessel Name': vessel_name,
                            'Total Running Days': f"{(total_running_hours_min/60)/24:,.2f}",
                            'MEShaftPowerActual (kW)': f"{weighted_avg_power:.2f}",
                            'LCVCorrectedFOC (MT/day)': f"{fuel_consumption_mt_per_day:.3f}"
                        })
            
            # Create and display the summary table for this speed range
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                
                st.dataframe(
                    summary_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Vessel": st.column_config.TextColumn(
                            "Vessel",
                            width="medium"
                        ),
                        "Total Running Days": st.column_config.TextColumn(
                            "Total Running Days",
                            width="medium"
                        ),
                        "MEShaftPowerActual (kW)": st.column_config.TextColumn(
                            "MEShaftPowerActual (kW)",
                            width="medium"
                        ),
                        "LCVCorrectedFOC (MT/day)": st.column_config.TextColumn(
                            "LCVCorrectedFOC (MT/day)",
                            width="medium"
                        )
                    }
                )
            else:
                st.info(f"No data available for any vessels in the {speed_min_range}-{speed_max_range} knots range.")

else:
    st.warning("⚠️ Please select at least one vessel from the sidebar to display the plot.")