import streamlit as st
from pymongo import MongoClient
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
    1004: "CASSIOPEIA*",
    1021: "PYXIS",
    1032: "Cenataurus",
    1016: "CHARA",
    1018: "CARINA*"
}

def generate_colors(n_colors):
    """Generate distinct colors for any number of vessels"""
    if n_colors <= 12:
        # Base color palette for up to 12 vessels - optimized for distinction
        base_scatter_colors = [
            "#E85252", "#6868CF", "#A8ECA8", "#F8B15F", "#D3ACEE", "#84EDED",
            "#F392C6", "#E6E97B", "#66AA63", "#FF6B35", "#4ECDC4", "#45B7D1"
        ]
        base_trendline_colors = [
            "#E70E0E", "#2B2BD0", "#6BEC6B", "#FA8C0F", "#BA71EF", "#00FFFF",
            "#F8349C", "#ECF406", "#335C33", "#CC4A00", "#2E8B8B", "#1E5799"
        ]
        return base_scatter_colors[:n_colors], base_trendline_colors[:n_colors]
    else:
        # Generate colors using plotly's color palette for more vessels
        colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Set1
        scatter_colors = colors[:n_colors]
        # Create darker versions for trendlines
        trendline_colors = []
        for color in scatter_colors:
            # Convert to darker version by reducing brightness
            if color.startswith('#'):
                # Convert hex to RGB, darken, convert back
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                r, g, b = max(0, r-40), max(0, g-40), max(0, b-40)
                darker_color = f"#{r:02x}{g:02x}{b:02x}"
                trendline_colors.append(darker_color)
            else:
                trendline_colors.append(color)
        
        return scatter_colors, trendline_colors

# Load your dataframe
try:
    mongo_uri = st.secrets["mongo"]["uri"]
    client = MongoClient(mongo_uri)
    db = client["seaker_data"]
    collection = db["combined_output_merged_input_nanremoved"]

    data = list(collection.find())
    df = pd.DataFrame(data)
    df.drop(columns=['_id'], inplace=True)

    df = df[(df["IsSpeedDropValid"]==1) & (df["IsDeltaPDOnSpeedValid"]==1)]
    df["LCVCorrectedFOC"] = df["ISOCorrectedFOC"] +df["MEFOCIdealPD"] - df["MEFOCIdealPDCor"]
    df = df[["VesselId", "MEShaftPowerActual", "ME1RunningHoursMinute", "MeanDraft", "RelativeWindDirection", "SpeedOG", "SpeedTW", "BFScale", "LCVCorrectedFOC"]].copy()
    
    # Load additional data
    casso_collection = db["cassiopeia_autolog_10min_rel_wind"]
    casso_data = list(casso_collection.find())
    df_cassiopeia = pd.DataFrame(casso_data)
    df_cassiopeia.drop(columns=['_id'], inplace=True)
    df_cassiopeia = df_cassiopeia[["VesselId", "MEShaftPowerActual", "ME1RunningHoursMinute", "MeanDraft", "RelativeWindDirection", "SpeedOG", "SpeedTW", "BFScale", "LCVCorrectedFOC"]].copy()
    df = pd.concat([df, df_cassiopeia], ignore_index=True)
    
except FileNotFoundError as e:
    st.error(f"CSV file not found: {e}")
    st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar for filters
st.sidebar.header("🔧 Filters")

# Speed Type Selection
st.sidebar.subheader("🚤 Speed Type Selection")
speed_type = st.sidebar.radio(
    "Select Speed Type:",
    options=["SpeedOG", "SpeedTW"],
    index=0,
    help="Choose between Speed Over Ground (SpeedOG) or Speed Through Water (SpeedTW)"
)

# Update title based on selection
st.title(f"🚢 MEShaftPowerActual vs {speed_type} Analysis")

# Get the selected speed column
speed_column = speed_type

# Get unique vessel IDs and create name options
unique_vessel_ids = sorted(df['VesselId'].unique())
vessel_name_options = [vessel_names.get(vid, f"Unknown_{vid}") for vid in unique_vessel_ids]

# Create a mapping for the multiselect
name_to_id = {vessel_names.get(vid, f"Unknown_{vid}"): vid for vid in unique_vessel_ids}

# Multiselect for vessels
selected_vessel_names = st.sidebar.multiselect(
    "Select Vessels:",
    options=vessel_name_options,
    default=vessel_name_options[:3],
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

# Dynamic Speed Filter
st.sidebar.subheader(f"🚤 {speed_type} Filter")
min_speed = df[speed_column].min()
max_speed = df[speed_column].max()

col5, col6 = st.sidebar.columns(2)
with col5:
    speed_min = st.number_input(
        f"Min {speed_type}:",
        min_value=float(min_speed),
        max_value=float(max_speed),
        value=float(min_speed),
        step=0.5,
        key=f"{speed_type.lower()}_min"
    )
with col6:
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

col7, col8 = st.sidebar.columns(2)
with col7:
    bf_min = st.number_input(
        "Min BF Scale:",
        min_value=float(min_bf),
        max_value=float(max_bf),
        value=float(min_bf),
        step=0.5,
        key="bf_min"
    )
with col8:
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
    try:
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
        
        if filtered_df.empty:
            st.warning("⚠️ No data available for the selected filters. Please adjust your filter criteria.")
        else:
            # Add vessel names to the dataframe for display
            filtered_df = filtered_df.copy()
            filtered_df['vessel_name'] = filtered_df['VesselId'].map(vessel_names)

            # Generate colors dynamically based on number of selected vessels
            n_vessels = len(selected_vessel_ids)
            scatter_colors, trendline_colors = generate_colors(n_vessels)

            fig = go.Figure()

            # Add scatter points
            for i, vessel_id in enumerate(selected_vessel_ids):
                vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
                vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
                
                if not vessel_data.empty:
                    fig.add_trace(go.Scatter(
                        x=vessel_data[speed_column],
                        y=vessel_data['MEShaftPowerActual'],
                        mode='markers',
                        name=vessel_name,
                        legendgroup=vessel_name,
                        marker=dict(
                            color=scatter_colors[i], 
                            size=8,
                            opacity=0.70,
                            line=dict(width=1.5, color='rgba(255,255,255,0.8)')
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

            # Add trendlines
            for i, vessel_id in enumerate(selected_vessel_ids):
                vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
                vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
                
                if len(vessel_data) > 3:
                    try:
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
                                width=4,
                                dash='solid'
                            ),
                            legendgroup=vessel_name,
                            showlegend=True,
                            hoverinfo='skip'
                        ))
                    except np.RankWarning:
                        st.warning(f"Could not fit polynomial for {vessel_name} - insufficient data variation")

            # Enhanced layout
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
                    bgcolor="rgba(0, 0, 0, 0)",
                    bordercolor="rgba(128, 128, 128, 0.5)",
                    borderwidth=1,
                    font=dict(color="rgba(128, 128, 128, 1)")
                ),
                margin=dict(r=180),
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                font=dict(color="rgba(128, 128, 128, 1)")
            )

            # Update axes
            fig.update_xaxes(
                gridcolor='rgba(128, 128, 128, 0.3)',
                gridwidth=1,
                griddash='dot',
                zeroline=True,
                zerolinecolor='rgba(128, 128, 128, 0.5)',
                zerolinewidth=1,
                title_font=dict(color="rgba(128, 128, 128, 1)"),
                tickfont=dict(color="rgba(128, 128, 128, 1)")
            )
            fig.update_yaxes(
                gridcolor='rgba(128, 128, 128, 0.3)',
                gridwidth=1,
                griddash='dot',
                zeroline=True,
                zerolinecolor='rgba(128, 128, 128, 0.5)',
                zerolinewidth=1,
                title_font=dict(color="rgba(128, 128, 128, 1)"),
                tickfont=dict(color="rgba(128, 128, 128, 1)")
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
                
                if len(speed_range_df) > 0:
                    st.write(f"\n ### {speed_type} in {speed_min_range}-{speed_max_range} knots")
                    
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
    
    except Exception as e:
        st.error(f"An error occurred while processing the data: {str(e)}")
        st.info("Please check your data and filter settings.")

else:
    st.warning("⚠️ Please select at least one vessel from the sidebar to display the plot.")