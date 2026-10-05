"""Weather Intelligence & Quantitative Climate Analytics Platform (Streamlit & Open-Meteo)."""

import datetime
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.openmeteo_client import OpenMeteoClient, decode_weather_code
from src.disasters_client import DisastersClient
from src.marine_space_client import MarineSpaceClient
from src.tectonic_data import identify_tectonic_plate
from src.analytics_engine import WeatherAnalyticsEngine
from src.visualizer import (
    create_forecast_overview_chart,
    create_daily_temperature_bands,
    create_wind_and_pressure_chart,
    create_degree_days_chart,
    create_climate_warming_chart,
    create_air_quality_gauge,
    create_pollutants_timeline_chart,
    create_aqi_comparison_chart,
    create_pollutants_radar,
    create_global_disasters_map,
    create_earthquake_distribution_chart,
    create_city_comparison_charts,
    create_marine_chart,
    create_space_weather_gauge,
    create_space_weather_history,
    create_soil_moisture_chart
)

# Configure Streamlit Page
st.set_page_config(
    page_title="Weather Intelligence & Climate Analytics",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 0.8rem;
    }
    .live-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #34d399;
        font-weight: 600;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0.3rem 0;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Clients
@st.cache_resource
def get_client() -> OpenMeteoClient:
    return OpenMeteoClient()

@st.cache_resource
def get_disasters_client() -> DisastersClient:
    return DisastersClient()

@st.cache_resource
def get_marine_space_client() -> MarineSpaceClient:
    return MarineSpaceClient()

client = get_client()
disasters_client = get_disasters_client()
marine_space_client = get_marine_space_client()

# Sidebar Controls
st.sidebar.markdown("## 🔍 Location & Search")

# Quick City Presets
PRESET_CITIES = {
    "Casablanca, Morocco 🇲🇦": {"name": "Casablanca", "lat": 33.5731, "lon": -7.5898, "tz": "Africa/Casablanca"},
    "Riyadh, Saudi Arabia 🇸🇦": {"name": "Riyadh", "lat": 24.7136, "lon": 46.6753, "tz": "Asia/Riyadh"},
    "Dubai, UAE 🇦🇪": {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "tz": "Asia/Dubai"},
    "New York, USA 🇺🇸": {"name": "New York", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    "London, UK 🇬🇧": {"name": "London", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
    "Paris, France 🇫🇷": {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris"},
    "Tokyo, Japan 🇯🇵": {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    "Singapore 🇸🇬": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"}
}

search_query = st.sidebar.text_input("Type any city name in the world:", value="", placeholder="e.g. Cairo, Madrid, Chicago...")

selected_location = None

if search_query:
    with st.sidebar:
        with st.spinner("Searching worldwide geocoding database..."):
            search_results = client.search_location(search_query)
            if search_results:
                options = {res["display_name"]: res for res in search_results}
                chosen_label = st.selectbox("Select matched location:", list(options.keys()))
                selected_location = options[chosen_label]
            else:
                st.warning("No locations found. Try another city name.")

if not selected_location:
    preset_choice = st.sidebar.selectbox("Or choose a major capital / hub:", list(PRESET_CITIES.keys()), index=0)
    preset_info = PRESET_CITIES[preset_choice]
    selected_location = {
        "name": preset_info["name"],
        "display_name": preset_choice,
        "latitude": preset_info["lat"],
        "longitude": preset_info["lon"],
        "timezone": preset_info["tz"]
    }

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Analytical Settings")
forecast_horizon = st.sidebar.slider("Forecast Days", min_value=3, max_value=16, value=14, step=1)
climate_start_year = st.sidebar.slider("Historical Archive Start Year", min_value=1950, max_value=2020, value=1980, step=5)

# 10s Live Auto-Refresh
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Live Telemetry & Auto-Refresh")
auto_refresh_enabled = st.sidebar.toggle("10s Auto-Refresh (Live Sync)", value=True)
refresh_counter = 0
if auto_refresh_enabled:
    refresh_counter = st_autorefresh(interval=10000, limit=None, key="weather_auto_refresh_10s")

# Main Dashboard View
city_name = selected_location.get("name", "Target City")
display_label = selected_location.get("display_name", city_name)
lat = selected_location["latitude"]
lon = selected_location["longitude"]
tz = selected_location.get("timezone", "auto")

# Detect Tectonic Plate for Current City
current_plate = identify_tectonic_plate(lat, lon)

st.markdown(f'<div class="main-title">🌦️ {display_label} — Weather & Earth Intelligence</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Coordinates: Lat <b>{lat:.4f}</b>, Lon <b>{lon:.4f}</b> | Timezone: <b>{tz}</b> | Crustal Plate: <b>{current_plate}</b></div>', unsafe_allow_html=True)

# Live Status Badge
now_utc_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
if auto_refresh_enabled:
    st.markdown(f'<div class="live-badge">🟢 LIVE TELEMETRY ACTIVE &bull; Auto-Refreshing every 10s &bull; Last Synced: {now_utc_str} &bull; Cycle #{refresh_counter}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="live-badge" style="background:rgba(148,163,184,0.1); border-color:rgba(148,163,184,0.3); color:#94a3b8;">⏸️ LIVE SYNC PAUSED &bull; Last Synced: {now_utc_str}</div>', unsafe_allow_html=True)

# Fetch Data
with st.spinner("Fetching real-time meteorology and climate data..."):
    forecast_data = client.fetch_forecast(lat, lon, timezone_str=tz, forecast_days=forecast_horizon)
    hourly_df = forecast_data.get("hourly_df", pd.DataFrame())
    daily_df = forecast_data.get("daily_df", pd.DataFrame())
    current_data = forecast_data.get("current", {})

if not current_data:
    st.error("Unable to load weather data. Please verify your connection or try another location.")
    st.stop()

# Real-Time Metrics Bar
curr_temp = current_data.get("temperature_2m", 0.0)
curr_feel = current_data.get("apparent_temperature", curr_temp)
curr_humidity = current_data.get("relative_humidity_2m", 0)
curr_wind = current_data.get("wind_speed_10m", 0.0)
curr_gust = current_data.get("wind_gusts_10m", curr_wind)
curr_pressure = current_data.get("pressure_msl", 1013.25)
curr_code = current_data.get("weather_code", 0)
weather_desc, weather_icon = decode_weather_code(curr_code)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Current Weather</div>
        <div class="metric-value">{weather_icon} {curr_temp:.1f}°C</div>
        <div class="metric-sub">{weather_desc}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Thermal Comfort</div>
        <div class="metric-value">🌡️ {curr_feel:.1f}°C</div>
        <div class="metric-sub">Feels Like</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Relative Humidity</div>
        <div class="metric-value">💧 {curr_humidity}%</div>
        <div class="metric-sub">Moisture Saturation</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Wind Velocity</div>
        <div class="metric-value">💨 {curr_wind:.1f} <span style="font-size:1rem;">km/h</span></div>
        <div class="metric-sub">Gusts up to {curr_gust:.1f} km/h</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Atmospheric Pressure</div>
        <div class="metric-value">⏲️ {curr_pressure:.1f} <span style="font-size:1rem;">hPa</span></div>
        <div class="metric-sub">Barometric Sea Level</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 11 Analytical Modules Tabs
tabs = st.tabs([
    "🔮 14-Day High-Res Forecast",
    "⚖️ Multi-City Comparison & Battle",
    "🌍 Historical Climate & Warming Trends",
    "⚡ Energy Degree Days (HDD / CDD)",
    "☀️ Renewable Energy Potential",
    "🌿 Air Quality & Environment",
    "🌊 Marine & Ocean Meteorology",
    "☀️ Space Weather & Solar Storms (NOAA)",
    "🌾 Agro-Meteorology & Soil Intelligence",
    "🚨 Anomaly & Extreme Weather (Z-Score)",
    "🌋 Geohazards, Earthquakes & Crustal Plates"
])

# ----------------- TAB 1: High-Res Forecast -----------------
with tabs[0]:
    st.markdown("### 🔮 High-Resolution Meteorological Forecast")
    
    fig_overview = create_forecast_overview_chart(hourly_df, city_name)
    st.plotly_chart(fig_overview, use_container_width=True)

    c1, c2 = st.columns([1.2, 1.0])
    with c1:
        fig_daily = create_daily_temperature_bands(daily_df, city_name)
        st.plotly_chart(fig_daily, use_container_width=True)
    with c2:
        fig_wind = create_wind_and_pressure_chart(hourly_df)
        st.plotly_chart(fig_wind, use_container_width=True)

    with st.expander("📋 View & Export Raw Hourly Forecast Dataset"):
        st.dataframe(hourly_df, use_container_width=True)
        csv_data = hourly_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Hourly Forecast CSV", data=csv_data, file_name=f"{city_name}_hourly_forecast.csv", mime="text/csv")

# ----------------- TAB 2: Multi-City Comparison & Battle -----------------
with tabs[1]:
    st.markdown("### ⚖️ Multi-City Meteorological Comparison & Benchmarking")
    st.markdown(f"Benchmark **{city_name}** side-by-side against any other global city.")

    cmp_col1, cmp_col2 = st.columns(2)
    with cmp_col1:
        st.info(f"**City A (Primary):** {display_label} (Lat {lat:.2f}, Lon {lon:.2f})")
    with cmp_col2:
        cmp_search = st.text_input("Search Second City to Compare (City B):", value="", placeholder="e.g. Tokyo, Dubai, London, New York...")
        cmp_location = None
        if cmp_search:
            cmp_res = client.search_location(cmp_search)
            if cmp_res:
                cmp_opts = {r["display_name"]: r for r in cmp_res}
                cmp_chosen = st.selectbox("Select matched second city:", list(cmp_opts.keys()))
                cmp_location = cmp_opts[cmp_chosen]
        if not cmp_location:
            # Default second preset (e.g. Dubai or London)
            fallback_key = "London, UK 🇬🇧" if "London" not in display_label else "Dubai, UAE 🇦🇪"
            cmp_location = {
                "name": PRESET_CITIES[fallback_key]["name"],
                "display_name": fallback_key,
                "latitude": PRESET_CITIES[fallback_key]["lat"],
                "longitude": PRESET_CITIES[fallback_key]["lon"],
                "timezone": PRESET_CITIES[fallback_key]["tz"]
            }

    city_b_name = cmp_location["name"]
    city_b_display = cmp_location.get("display_name", city_b_name)
    lat_b = cmp_location["latitude"]
    lon_b = cmp_location["longitude"]
    tz_b = cmp_location.get("timezone", "auto")

    with st.spinner(f"Fetching forecast for {city_b_name}..."):
        forecast_b = client.fetch_forecast(lat_b, lon_b, timezone_str=tz_b, forecast_days=forecast_horizon)
        hourly_df_b = forecast_b.get("hourly_df", pd.DataFrame())
        current_b = forecast_b.get("current", {})

    if not current_b or hourly_df_b.empty:
        st.warning(f"Unable to fetch comparison data for {city_b_name}.")
    else:
        # Comparison Metrics
        temp_a = curr_temp
        temp_b = current_b.get("temperature_2m", 0.0)
        diff_temp = temp_a - temp_b

        hum_a = curr_humidity
        hum_b = current_b.get("relative_humidity_2m", 0)

        wind_a = curr_wind
        wind_b = current_b.get("wind_speed_10m", 0.0)

        st.markdown(f"#### 🥊 Live Head-to-Head: **{city_name}** vs **{city_b_name}**")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(f"🌡️ Temperature", f"{temp_a:.1f}°C vs {temp_b:.1f}°C", delta=f"{diff_temp:+.1f}°C diff")
        k2.metric(f"💧 Humidity", f"{hum_a}% vs {hum_b}%", delta=f"{hum_a - hum_b:+d}% diff")
        k3.metric(f"💨 Wind Speed", f"{wind_a:.1f} vs {wind_b:.1f} km/h", delta=f"{wind_a - wind_b:+.1f} km/h")
        k4.metric(f"⏲️ Pressure", f"{curr_pressure:.1f} vs {current_b.get('pressure_msl', 1013):.1f} hPa")

        # Visual Comparison Chart
        fig_cmp = create_city_comparison_charts(hourly_df, hourly_df_b, city_name, city_b_name)
        st.plotly_chart(fig_cmp, use_container_width=True)

# ----------------- TAB 3: Historical Climate -----------------
with tabs[2]:
    st.markdown("### 🌍 Multi-Decade Historical Climate Archive (1950 - Present)")
    st.info("Fetches daily climate records from the global ECMWF/ERA5 atmospheric reanalysis model archive.")

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    start_str = f"{climate_start_year}-01-01"

    if st.button("🚀 Load Multi-Decade Climate Archive", key="btn_hist"):
        with st.spinner(f"Aggregating climate data from {start_str} to {today_str}..."):
            hist_df = client.fetch_historical_climate(lat, lon, start_date=start_str, end_date=today_str, timezone_str=tz)
            if not hist_df.empty:
                trend_res = WeatherAnalyticsEngine.calculate_climate_warming_trend(hist_df)
                annual_df = trend_res["annual_df"]
                slope = trend_res["slope_c_per_decade"]
                r2 = trend_res["r_squared"]
                narrative = trend_res["warming_narrative"]

                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Warming Trend Rate", f"{slope:+.3f} °C / decade", delta=narrative)
                mc2.metric("Regression Fit ($R^2$)", f"{r2:.3f}")
                mc3.metric("Years Analyzed", f"{len(annual_df)} Years")

                fig_climate = create_climate_warming_chart(annual_df, city_name, slope)
                st.plotly_chart(fig_climate, use_container_width=True)
            else:
                st.warning("Historical data currently unavailable for this coordinate range.")

# ----------------- TAB 4: Energy Degree Days -----------------
with tabs[3]:
    st.markdown("### ⚡ Energy Demand Profiling: Heating (HDD) & Cooling (CDD) Degree Days")
    st.markdown("""
    - **Heating Degree Days (HDD)**: $\\max(0, 18.0 - T_{mean})$ — Measures natural gas & heating fuel demand.
    - **Cooling Degree Days (CDD)**: $\\max(0, T_{mean} - 18.0)$ — Measures air conditioning & peak summer electricity grid load.
    """)

    if not daily_df.empty:
        dd_df = WeatherAnalyticsEngine.compute_degree_days(daily_df, base_temp_c=18.0)
        tot_hdd = dd_df["HDD"].sum()
        tot_cdd = dd_df["CDD"].sum()

        ec1, ec2 = st.columns(2)
        ec1.metric("Projected Heating Load (Total HDD)", f"{tot_hdd:.1f} °C-days")
        ec2.metric("Projected Cooling Load (Total CDD)", f"{tot_cdd:.1f} °C-days")

        fig_dd = create_degree_days_chart(dd_df)
        st.plotly_chart(fig_dd, use_container_width=True)

# ----------------- TAB 5: Renewable Potential -----------------
with tabs[4]:
    st.markdown("### ☀️ Renewable Energy Potential Index")
    st.markdown("Estimates Solar PV output and Wind Power Density derived from hourly meteorological variables.")

    if not hourly_df.empty:
        renew_res = WeatherAnalyticsEngine.calculate_renewable_potential(hourly_df)
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("Avg Solar PV Index", f"{renew_res['avg_solar_index']} W/m²")
        rc2.metric("Peak Solar PV Yield", f"{renew_res['peak_solar_index']} W/m²")
        rc3.metric("Avg Wind Power Density", f"{renew_res['avg_wind_density_w_m2']} W/m²")
        rc4.metric("Peak Wind Density", f"{renew_res['peak_wind_density_w_m2']} W/m²")

        st.line_chart(renew_res["enriched_df"].set_index("time")[["solar_pv_index_w_m2", "wind_power_density_w_m2"]])

# ----------------- TAB 6: Air Quality -----------------
with tabs[5]:
    st.markdown("### 🌿 Atmospheric Composition, Air Quality & Health Intelligence")
    with st.spinner("Fetching atmospheric pollutants and aerosol models..."):
        aq_df = client.fetch_air_quality(lat, lon, timezone_str=tz)
        
        if not aq_df.empty:
            latest_aq = aq_df.iloc[-1].to_dict()
            us_aqi = latest_aq.get("us_aqi", 45)
            eu_aqi = latest_aq.get("european_aqi", 20)
            pm25 = latest_aq.get("pm2_5", 0.0)
            pm10 = latest_aq.get("pm10", 0.0)
            no2 = latest_aq.get("nitrogen_dioxide", 0.0)
            o3 = latest_aq.get("ozone", 0.0)
            so2 = latest_aq.get("sulphur_dioxide", 0.0)
            co = latest_aq.get("carbon_monoxide", 0.0)

            # Health category descriptor
            if us_aqi <= 50:
                aqi_badge = "🟢 Good (Satisfactory Air Quality)"
                aqi_advise = "Air quality is considered satisfactory, and air pollution poses little or no risk. Great time for outdoor activities!"
            elif us_aqi <= 100:
                aqi_badge = "🟡 Moderate (Acceptable Air Quality)"
                aqi_advise = "Air quality is acceptable; however, unusually sensitive individuals should consider limiting prolonged outdoor exertion."
            elif us_aqi <= 150:
                aqi_badge = "🟠 Unhealthy for Sensitive Groups"
                aqi_advise = "Members of sensitive groups (asthma, children, elderly) may experience health effects. General public is less likely to be affected."
            elif us_aqi <= 200:
                aqi_badge = "🔴 Unhealthy (Increased Health Risk)"
                aqi_advise = "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects. Reduce outdoor activities."
            else:
                aqi_badge = "🟣 Very Unhealthy / Hazardous ⚠️"
                aqi_advise = "Health alert: The risk of health effects is increased for everyone. Avoid outdoor exertion and keep windows closed."

            st.info(f"**Health Advisory Status: {aqi_badge}**\n\n{aqi_advise}")

            # Top KPI Metric Row
            aq_c1, aq_c2, aq_c3, aq_c4, aq_c5, aq_c6 = st.columns(6)
            aq_c1.metric("PM2.5 Fine Particles", f"{pm25:.1f} µg/m³", delta="Safe ≤ 15" if pm25 <= 15 else "Elevated", delta_color="normal" if pm25 <= 15 else "inverse")
            aq_c2.metric("PM10 Dust Particles", f"{pm10:.1f} µg/m³", delta="Safe ≤ 45" if pm10 <= 45 else "Elevated", delta_color="normal" if pm10 <= 45 else "inverse")
            aq_c3.metric("Nitrogen Dioxide (NO₂)", f"{no2:.1f} µg/m³", delta="Traffic / Smog")
            aq_c4.metric("Ozone (O₃)", f"{o3:.1f} µg/m³", delta="Photochemical")
            aq_c5.metric("Sulfur Dioxide (SO₂)", f"{so2:.1f} µg/m³", delta="Industrial")
            aq_c6.metric("Carbon Monoxide (CO)", f"{co:.0f} µg/m³", delta="Combustion")

            st.markdown("<br>", unsafe_allow_html=True)

            # Charts Row 1: Gauge & Radar + AQI Comparison
            r1_col1, r1_col2 = st.columns([1, 1.2])
            with r1_col1:
                fig_gauge = create_air_quality_gauge(us_aqi, "US EPA Air Quality Index")
                st.plotly_chart(fig_gauge, use_container_width=True)
                
                fig_radar = create_pollutants_radar(latest_aq)
                st.plotly_chart(fig_radar, use_container_width=True)

            with r1_col2:
                fig_aqi_comp = create_aqi_comparison_chart(aq_df)
                st.plotly_chart(fig_aqi_comp, use_container_width=True)

            # Charts Row 2: Comprehensive 72h Chemical Timeline
            fig_timeline = create_pollutants_timeline_chart(aq_df)
            st.plotly_chart(fig_timeline, use_container_width=True)

            with st.expander("📋 View & Export Raw Hourly Air Quality Dataset"):
                p_cols = [c for c in ["pm2_5", "pm10", "nitrogen_dioxide", "ozone", "sulphur_dioxide", "carbon_monoxide", "us_aqi", "european_aqi", "dust"] if c in aq_df.columns]
                st.dataframe(aq_df[["time"] + p_cols].tail(72).reset_index(drop=True), use_container_width=True)
                csv_aq = aq_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Air Quality CSV", data=csv_aq, file_name=f"{city_name}_air_quality.csv", mime="text/csv")
        else:
            st.warning("Air quality data is temporarily unavailable for this coordinate.")

# ----------------- TAB 7: Marine & Ocean Meteorology -----------------
with tabs[6]:
    st.markdown("### 🌊 Marine & Ocean Meteorology Forecast")
    st.markdown("Provides high-resolution wave height, swell dynamics, and wave periods for maritime, shipping, and coastal zones.")
    
    with st.spinner("Fetching oceanographic wave & swell models..."):
        marine_df = marine_space_client.fetch_marine_weather(lat, lon, timezone_str=tz)

    if not marine_df.empty:
        latest_marine = marine_df.iloc[0]
        sig_wave = latest_marine.get("wave_height", 0.0)
        swell_h = latest_marine.get("swell_wave_height", 0.0)
        wave_p = latest_marine.get("wave_period", 0.0)
        swell_p = latest_marine.get("swell_wave_period", 0.0)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Significant Wave Height", f"{sig_wave:.2f} m", delta="Calm" if sig_wave < 1.25 else "Moderate/Rough")
        m2.metric("Swell Wave Height", f"{swell_h:.2f} m")
        m3.metric("Wave Period", f"{wave_p:.1f} sec")
        m4.metric("Swell Period", f"{swell_p:.1f} sec")

        fig_marine = create_marine_chart(marine_df, city_name)
        st.plotly_chart(fig_marine, use_container_width=True)
    else:
        st.info(f"ℹ️ **{city_name}** appears to be an inland terrestrial location. Open-Meteo Marine models are specialized for ocean and coastal coordinates. (Try selecting coastal cities like Casablanca, Tokyo, Singapore, or New York to inspect live sea waves).")

# ----------------- TAB 8: Space Weather & Solar Storms -----------------
with tabs[7]:
    st.markdown("### ☀️ Space Weather & Solar Storm Intelligence (NOAA SWPC)")
    st.markdown("Real-time solar activity and geomagnetic storm monitoring from the NOAA Space Weather Prediction Center.")

    with st.spinner("Fetching real-time NOAA Planetary Kp index..."):
        space_data = marine_space_client.fetch_space_weather()

    curr_kp = space_data["current_kp"]
    storm_lvl = space_data["storm_level"]
    aurora_msg = space_data["aurora_impact"]
    time_utc = space_data["time_utc"]
    df_kp = space_data["kp_history_df"]

    st.info(f"**Geomagnetic Storm Status: {storm_lvl}** (Observation Time: {time_utc})\n\n🌌 **Aurora & Ionosphere Impact:** {aurora_msg}")

    sp1, sp2 = st.columns([1, 1.3])
    with sp1:
        fig_kp_gauge = create_space_weather_gauge(curr_kp)
        st.plotly_chart(fig_kp_gauge, use_container_width=True)
    with sp2:
        fig_kp_hist = create_space_weather_history(df_kp)
        st.plotly_chart(fig_kp_hist, use_container_width=True)

    with st.expander("📚 NOAA Space Weather Storm Scale Reference"):
        st.markdown("""
        | Scale | Condition | Planetary $Kp$ | Terrestrial & Satellite Impacts |
        | :--- | :--- | :--- | :--- |
        | **G0** | Quiet / Unsettled | $Kp < 5$ | Nominal space environment; polar aurora only. |
        | **G1** | Minor Storm | $Kp = 5$ | Weak power grid fluctuations; minor satellite operations impacts. |
        | **G2** | Moderate Storm | $Kp = 6$ | High-latitude power systems experience voltage alarms; HF radio fade. |
        | **G3** | Strong Storm | $Kp = 7$ | Satellite orientation issues; GPS satellite navigation degradation. |
        | **G4** | Severe Storm | $Kp = 8$ | Widespread voltage control problems; HF blackouts. Aurora down to mid-latitudes. |
        | **G5** | Extreme Storm | $Kp = 9$ | Complete high-frequency radio blackouts; power grid collapse risks. |
        """)

# ----------------- TAB 9: Agro-Meteorology & Soil Intelligence -----------------
with tabs[8]:
    st.markdown("### 🌾 Agro-Meteorology, Soil Stratification & Irrigation Intelligence")
    st.markdown("Precision agriculture metrics based on the FAO-56 Penman-Monteith Evapotranspiration model and multi-depth soil moisture sensors.")

    if not hourly_df.empty and "soil_moisture_0_to_1cm" in hourly_df.columns:
        latest_hour = hourly_df.iloc[-1]
        s_0_1 = latest_hour.get("soil_moisture_0_to_1cm", 0.0)
        s_3_9 = latest_hour.get("soil_moisture_3_to_9cm", 0.0)
        vpd_val = latest_hour.get("vapour_pressure_deficit", 0.0)
        tot_et0 = hourly_df.get("et0_fao_evapotranspiration", pd.Series([0.0])).sum()

        ag1, ag2, ag3, ag4 = st.columns(4)
        ag1.metric("Topsoil Moisture (0-1cm)", f"{s_0_1:.3f} m³/m³", delta="Surface Layer")
        ag2.metric("Root Zone Moisture (3-9cm)", f"{s_3_9:.3f} m³/m³", delta="Plant Roots")
        ag3.metric("Vapor Pressure Deficit (VPD)", f"{vpd_val:.2f} kPa", delta="Optimal 0.8-1.2 kPa" if 0.8 <= vpd_val <= 1.2 else "Stress Risk")
        ag4.metric("Forecast Cumulative ET₀", f"{tot_et0:.1f} mm", delta="Total Crop Water Loss")

        fig_soil = create_soil_moisture_chart(hourly_df, city_name)
        st.plotly_chart(fig_soil, use_container_width=True)
    else:
        st.warning("Agro-meteorological soil moisture data not available for this run.")

# ----------------- TAB 10: Anomaly Detection -----------------
with tabs[9]:
    st.markdown("### 🚨 Weather Anomaly & Extreme Event Detection (Z-Score)")
    st.markdown("Identifies statistically anomalous temperature spikes (Heatwaves) or drops (Cold Snaps) where $|Z| > 1.5$.")

    if not daily_df.empty:
        anom_df = WeatherAnalyticsEngine.detect_temperature_anomalies(daily_df, temp_col="temperature_2m_max", window=7)
        st.dataframe(
            anom_df[["time", "temperature_2m_max", "rolling_mean", "z_score", "anomaly_type"]].rename(columns={
                "time": "Date",
                "temperature_2m_max": "Max Temp (°C)",
                "rolling_mean": "7-Day Benchmark (°C)",
                "z_score": "Z-Score",
                "anomaly_type": "Classification"
            }),
            use_container_width=True
        )

# ----------------- TAB 11: Geohazards, Earthquakes & Crustal Plates -----------------
with tabs[10]:
    st.markdown("### 🌋 Global Natural Disasters, Geohazards & Tectonic Plates (USGS & NASA)")
    st.markdown(f"Live worldwide geohazard tracking combining **USGS Earthquakes & Tsunami Warnings**, **Tectonic Plate Fault Lines (Earth's Crust)**, and **NASA EONET Satellite Feeds** (Tropical Cyclones, Volcanic Eruptions & Wildfires).")

    # Tectonic Plate Badge for Selected City
    st.info(f"🧩 **Geotectonic Crustal Classification for {city_name}:** Located on the **{current_plate}**.")

    # Filter Controls
    dc1, dc2 = st.columns([1.5, 1])
    with dc1:
        quake_feed = st.selectbox(
            "USGS Earthquake Timeframe Feed:",
            options=["all_week", "all_day", "4.5_month", "significant_month"],
            format_func=lambda x: {
                "all_week": "Past 7 Days (Worldwide All Magnitudes M 2.5+)",
                "all_day": "Past 24 Hours (Real-Time Live)",
                "4.5_month": "Past 30 Days (Moderate to Major M 4.5+)",
                "significant_month": "Past 30 Days (Major Catastrophic Significant Events)"
            }[x],
            index=0
        )
    with dc2:
        min_mag = st.slider("Minimum Richter Magnitude (M)", min_value=2.5, max_value=7.0, value=3.0, step=0.5)

    with st.spinner("Fetching global seismological, tectonic and satellite disaster feeds..."):
        earthquakes_df = disasters_client.fetch_usgs_earthquakes(feed=quake_feed, min_magnitude=min_mag)
        nasa_events_df = disasters_client.fetch_nasa_eonet_events(days=30)
        nearest_df = disasters_client.find_nearest_hazards(lat, lon, earthquakes_df, nasa_events_df, top_n=8)

    # Top Disaster KPI Summary Cards
    tot_quakes = len(earthquakes_df)
    max_quake_mag = earthquakes_df["magnitude"].max() if not earthquakes_df.empty else 0.0
    max_quake_row = earthquakes_df.iloc[0] if not earthquakes_df.empty else None
    max_quake_place = max_quake_row["place"] if max_quake_row is not None else "None"
    
    tsunami_alerts_count = int(earthquakes_df["tsunami_warning"].sum()) if not earthquakes_df.empty else 0
    nasa_storms_count = len(nasa_events_df[nasa_events_df["category"].str.contains("Storm|Cyclone", case=False)]) if not nasa_events_df.empty else 0
    nasa_volcano_count = len(nasa_events_df[nasa_events_df["category"].str.contains("Volcano", case=False)]) if not nasa_events_df.empty else 0

    dk1, dk2, dk3, dk4, dk5 = st.columns(5)
    dk1.metric("Active Earthquakes", f"{tot_quakes} Events", delta=f"Feed: {quake_feed}")
    dk2.metric("Max Recorded Mag", f"M {max_quake_mag:.1f}", delta=max_quake_place[:20])
    dk3.metric("🚨 Tsunami Alerts", f"{tsunami_alerts_count} Active", delta="USGS Warning" if tsunami_alerts_count > 0 else "Normal", delta_color="inverse" if tsunami_alerts_count > 0 else "normal")
    dk4.metric("🌀 Active Cyclones", f"{nasa_storms_count} Tracked", delta="NASA EONET")
    dk5.metric("🌋 Active Volcanoes", f"{nasa_volcano_count} Eruptions", delta="NASA Satellite")

    st.markdown("<br>", unsafe_allow_html=True)

    # Global Hazard Map
    st.markdown("#### 🗺️ Interactive Global Hazard Map (Tectonic Plates, Earthquakes, Tsunamis, Cyclones & Volcanoes)")
    fig_disaster_map = create_global_disasters_map(earthquakes_df, nasa_events_df, user_lat=lat, user_lon=lon, user_city=city_name)
    st.plotly_chart(fig_disaster_map, use_container_width=True)

    # Proximity Radar: Distance to Nearest Hazards
    st.markdown(f"#### 📡 Proximity Risk Radar: Closest Active Hazards to **{city_name}**")
    if not nearest_df.empty:
        closest_event = nearest_df.iloc[0]
        st.warning(f"⚠️ **Closest Active Geohazard**: **{closest_event['hazard_type']}** located **{closest_event['distance_km']:,.1f} km** away at *{closest_event['name_location']}* ({closest_event['magnitude_details']}).")
        
        st.dataframe(
            nearest_df[["hazard_type", "name_location", "distance_km", "magnitude_details", "time_utc", "source"]].rename(columns={
                "hazard_type": "Hazard Type",
                "name_location": "Location / Event Title",
                "distance_km": "Distance from City (km)",
                "magnitude_details": "Intensity / Depth",
                "time_utc": "Timestamp (UTC)",
                "source": "Agency"
            }),
            use_container_width=True
        )
    else:
        st.success(f"✅ No active major geohazards detected within reporting range of {city_name}.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Dual Tables: Earthquakes Feed & NASA Active Events Feed
    feed_col1, feed_col2 = st.columns(2)
    with feed_col1:
        st.markdown("#### 💥 USGS Worldwide Earthquakes Feed")
        if not earthquakes_df.empty:
            st.dataframe(
                earthquakes_df[["place", "magnitude", "depth_km", "time_utc", "tsunami_warning"]].head(25).rename(columns={
                    "place": "Location",
                    "magnitude": "Magnitude (M)",
                    "depth_km": "Depth (km)",
                    "time_utc": "Time (UTC)",
                    "tsunami_warning": "Tsunami Warning"
                }),
                use_container_width=True
            )
        else:
            st.info("No earthquakes matching the magnitude threshold.")

    with feed_col2:
        st.markdown("#### 🌀 NASA EONET Active Extreme Events")
        if not nasa_events_df.empty:
            st.dataframe(
                nasa_events_df[["title", "category", "intensity", "date_utc"]].head(25).rename(columns={
                    "title": "Disaster Title",
                    "category": "Classification",
                    "intensity": "Intensity",
                    "date_utc": "Date (UTC)"
                }),
                use_container_width=True
            )
        else:
            st.info("No active NASA events reported.")

    # Earthquake Magnitude vs Depth Distribution
    if not earthquakes_df.empty:
        fig_dist = create_earthquake_distribution_chart(earthquakes_df)
        st.plotly_chart(fig_dist, use_container_width=True)


