import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import math



# Page configuration
st.set_page_config(page_title="Vessel MEShaftPowerActual vs SpeedTW Analysis", layout="wide")

# Title
st.title("🚢 MEShaftPowerActual vs SpeedTW Analysis")

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

st.sidebar.subheader("🚤 SpeedTW Filter")
min_sog = df['SpeedTW'].min()
max_sog = df['SpeedTW'].max()

col3, col4 = st.sidebar.columns(2)
with col3:
    sog_min = st.number_input(
        "Min SpeedTW:",
        min_value=float(min_sog),
        max_value=float(max_sog),
        value=float(min_sog),
        step=0.5,
        key="sog_min"
    )
with col4:
    sog_max = st.number_input(
        "Max SpeedTW:",
        min_value=float(min_sog),
        max_value=float(max_sog),
        value=float(max_sog),
        step=0.5,
        key="sog_max"
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

# Apply all filters to the dataframe (replace the existing filtering section)
if selected_vessel_ids:
    # Filter by vessel IDs
    filtered_df = df[df['VesselId'].isin(selected_vessel_ids)]
    
    
    filtered_df = filtered_df[
        (filtered_df['MeanDraft'] >= draft_min) & 
        (filtered_df['MeanDraft'] <= draft_max) & 
        (filtered_df['RelativeWindDirection'] >= wind_min) & 
        (filtered_df['RelativeWindDirection'] <= wind_max)& 
        (filtered_df['SpeedTW'] >= sog_min) &
        (filtered_df['SpeedTW'] <= sog_max)&
        (filtered_df['BFScale'] >= bf_min) &
        (filtered_df['BFScale'] <= bf_max)

    ]

    
    # Add vessel names to the dataframe for display
    filtered_df = filtered_df.copy()
    filtered_df['vessel_name'] = filtered_df['VesselId'].map(vessel_names)
    

    
    

    

    # One palette for scatter points, another for trendlines
    scatter_palette = px.colors.qualitative.Set3        # For points
    trendline_palette = px.colors.qualitative.Plotly    # For lines (high contrast vs Set3)

    fig = go.Figure()

    for i, vessel_id in enumerate(selected_vessel_ids):
        vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
        vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
        scatter_color = scatter_palette[i % len(scatter_palette)]
        fig.add_trace(go.Scatter(
            x=vessel_data['SpeedTW'],
            y=vessel_data['MEShaftPowerActual'],
            mode='markers',
            name=vessel_name,
            legendgroup=vessel_name,
            marker=dict(color=scatter_color, size=7, opacity=0.60),
            showlegend=True,
            customdata=np.stack((vessel_data['SpeedTW'], vessel_data['MEShaftPowerActual'], vessel_data['VesselId']), axis=-1),
            hovertemplate=(
                f"Vessel: {vessel_name}<br>"
                # "Vessel ID: %{customdata[2]}<br>"
                "SpeedTW: %{customdata[0]:.2f} knots<br>"
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
            vessel_data_sorted = vessel_data.sort_values('SpeedTW')
            coeffs = np.polyfit(vessel_data_sorted['SpeedTW'], vessel_data_sorted['MEShaftPowerActual'], 3)
            poly_func = np.poly1d(coeffs)
            x_smooth = np.linspace(vessel_data_sorted['SpeedTW'].min(), vessel_data_sorted['SpeedTW'].max(), 100)
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
        # title="MEShaftPowerActual vs SpeedTW",
        xaxis_title='SpeedTW (knots)',
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
    
    # Create Summary Table
    # st.subheader("📊 Vessel Summary Statistics")
    
    # summary_data = []
    
    # for vessel_id in selected_vessel_ids:
    #     vessel_data = filtered_df[filtered_df['VesselId'] == vessel_id]
    #     vessel_name = vessel_names.get(vessel_id, f"Unknown_{vessel_id}")
        
    #     if len(vessel_data) > 0:
    #         # Calculate weighted averages using ME1RunningHoursMinute as weights
    #         total_running_hours_min = vessel_data['ME1RunningHoursMinute'].sum()
            
    #         if total_running_hours_min > 0:
    #             # Weighted average for SpeedTW
    #             weighted_avg_speed = (vessel_data['SpeedTW'] * vessel_data['ME1RunningHoursMinute']).sum() / total_running_hours_min
                
    #             # Weighted average for MEShaftPowerActual
    #             weighted_avg_power = (vessel_data['MEShaftPowerActual'] * vessel_data['ME1RunningHoursMinute']).sum() / total_running_hours_min
                
    #             # Calculate LCVCorrectedFOC: Total fuel consumed / total running hours * minutes per day
    #             total_fuel_consumed = vessel_data['LCVCorrectedFOC'].sum()  # Total MT
    #             fuel_consumption_mt_per_minute = total_fuel_consumed / total_running_hours_min
    #             fuel_consumption_mt_per_day = fuel_consumption_mt_per_minute * 1440  # 1440 minutes in a day
                
    #             # Add to summary data
    #             summary_data.append({
    #                 'Vessel Name': vessel_name,
    #                 # 'Data Points': len(vessel_data),
    #                 'Total Running Days': f"{(total_running_hours_min/60)/24:,.2f}",
    #                 'Avg SpeedTW (knots)': f"{weighted_avg_speed:.2f}",
    #                 'Avg MEShaftPowerActual (kW)': f"{weighted_avg_power:.2f}",
    #                 'Avg LCVCorrectedFOC (MT/day)': f"{fuel_consumption_mt_per_day:.3f}"
    #             })
    
    # # Create and display the summary table
    # if summary_data:
    #     summary_df = pd.DataFrame(summary_data)
        
    #     # Style the dataframe for better presentation
    #     st.dataframe(
    #         summary_df,
    #         use_container_width=True,
    #         hide_index=True,
    #         column_config={
    #             "Vessel Name": st.column_config.TextColumn(
    #                 "Vessel Name",
    #                 width="medium"
    #             ),
    #             # "Data Points": st.column_config.NumberColumn(
    #             #     "Data Points",
    #             #     format="%d"
    #             # ),
    #             "Total Running Hours": st.column_config.TextColumn(
    #                 "Total Running Hours",
    #                 width="medium"
    #             ),
    #             "Avg SpeedTW (knots)": st.column_config.TextColumn(
    #                 "Avg SpeedTW (knots)",
    #                 width="small"
    #             ),
    #             "Avg MEShaftPowerActual (kW)": st.column_config.TextColumn(
    #                 "Avg MEShaftPowerActual (kW)",
    #                 width="medium"
    #             ),
    #             "LCVCorrectedFOC (MT/day)": st.column_config.TextColumn(
    #                 "LCVCorrectedFOC (MT/day)",
    #                 width="medium"
    #             )
    #         }
    #     )
    # Create Summary Tables for Speed Ranges
    st.subheader("📊 Speed Range Analysis")
    
    # Define speed ranges with step of 1
    min_speed = math.floor(filtered_df['SpeedTW'].min())
    max_speed = math.ceil(filtered_df['SpeedTW'].max())
    speed_ranges = [(i, i+1) for i in range(min_speed, max_speed)]
    
    for speed_min, speed_max in speed_ranges:
        # Filter data for this speed range
        speed_range_df = filtered_df[
            (filtered_df['SpeedTW'] >= speed_min) & 
            (filtered_df['SpeedTW'] < speed_max)
        ]
        
        if len(speed_range_df) > 0:  # Only show ranges that have data
            st.write(f"\n### SpeedTW in {speed_min}-{speed_max} knots")
            
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
                st.info(f"No data available for any vessels in the {speed_min}-{speed_max} knots range.")
        
        # Add some explanatory text
        # st.caption("📝 **Note:** SpeedTW and MEShaftPowerActual are weighted averages using ME1RunningHoursMinute as weights. LCVCorrectedFOC is calculated as total fuel consumed divided by total running hours, then converted to MT/day.")
    
    else:
        # st.warning("⚠️ No data available for the selected vessels with current filters.")
        pass

else:
    st.warning("⚠️ Please select at least one vessel from the sidebar to display the plot.")