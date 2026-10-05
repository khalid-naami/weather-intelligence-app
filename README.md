# 🌦️ Weather Intelligence & Quantitative Climate Analytics Platform

An institutional-grade **Streamlit** analytics application powered by the **Open-Meteo API** (100% Free, No API Key required). The platform delivers high-resolution real-time forecasts, multi-decade climate trend analysis, energy demand modeling (HDD/CDD), renewable energy potential estimations, and extreme weather anomaly detection for any location worldwide.

---

## 🌟 Core Analytical Modules

1. **🔮 14-Day High-Resolution Meteorological Forecast**:
   - Hourly and daily predictions for Temperature, Apparent Temperature ("Feels Like"), Relative Humidity, Precipitation (mm & %), Barometric Sea-Level Pressure, Wind Speed, Gusts, and Cloud Cover.
   - Interactive dual-axis Plotly charts and diurnal temperature range envelopes.

2. **🌍 Multi-Decade Historical Climate & Warming Trends (1950 - Present)**:
   - Deep integration with global atmospheric reanalysis archives (ECMWF ERA5).
   - Automated OLS regression calculating the regional **warming rate in °C per decade** alongside $R^2$ statistical goodness-of-fit.

3. **⚡ Energy Demand Profiling (HDD & CDD)**:
   - **Heating Degree Days (HDD)**: $\max(0, 18.0 - T_{\text{mean}})$ — Proxy for residential/commercial heating fuel and natural gas demand.
   - **Cooling Degree Days (CDD)**: $\max(0, T_{\text{mean}} - 18.0)$ — Proxy for air conditioning load and peak summer power grid strain.

4. **☀️ Renewable Energy Potential Index**:
   - **Solar PV Yield Potential**: Direct Normal Irradiance ($W/m^2$) adjusted for high-temperature PV thermal degradation.
   - **Wind Power Density**: Cubic kinetic power density ($P = \frac{1}{2} \rho v^3$) in $W/m^2$.

5. **🌿 Atmospheric Health & Air Quality**:
   - Real-time US EPA and European Air Quality Index (AQI) gauges.
   - Fine particulate matter ($PM_{2.5}$, $PM_{10}$), Nitrogen Dioxide ($NO_2$), Ozone ($O_3$), and Sulfur Dioxide ($SO_2$) tracking.

6. **🚨 Anomaly & Extreme Weather Detection**:
   - Dynamic rolling $Z\text{-Score}$ statistical anomaly detection identifying Heatwaves ($Z > +1.5$) and Cold Snaps ($Z < -1.5$).

---

## 🚀 Quickstart & Installation

### 1. Clone or Navigate to the Directory
```bash
cd C:\Users\khali\OneDrive\Bureau\weather-intelligence-app
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Streamlit App
```bash
streamlit run app.py
```

The application will automatically launch in your browser at `http://localhost:8501`.

---

## 📁 Project Architecture

```
weather-intelligence-app/
├── app.py                      # Main Streamlit Dashboard
├── requirements.txt            # Python Dependencies
├── README.md                   # Documentation
└── src/
    ├── __init__.py
    ├── openmeteo_client.py     # Open-Meteo Geocoding, Forecast, Archive & AQI API Client
    ├── analytics_engine.py     # HDD/CDD, Z-Score Anomaly, Solar/Wind & Climate Trends Engine
    └── visualizer.py           # High-Performance Plotly Charts & Gauges
```

---

## 📜 License
MIT License. Built for meteorologists, data scientists, energy analysts, commodity traders, and quantitative researchers.
