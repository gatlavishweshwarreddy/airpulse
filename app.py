import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.6-flash')


WAQI_TOKEN = os.environ.get("WAQI_TOKEN")

def get_aqi(city):
    url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
    response = requests.get(url)
    data = response.json()
    if data["status"] == "ok":
        return data["data"]
    return None

def get_aqi_color(aqi):
    if aqi <= 50: return "#10b981", "Good"
    elif aqi <= 100: return "#f59e0b", "Moderate"
    elif aqi <= 150: return "#f97316", "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "#ef4444", "Unhealthy"
    elif aqi <= 300: return "#8b5cf6", "Very Unhealthy"
    else: return "#7f1d1d", "Hazardous"

def get_eco_tips(aqi, city):
    prompt = f"""You are AirPulse, an environmental AI advisor.
City: {city}, AQI: {aqi}
Give 3 specific hyperlocal eco tips to REDUCE air pollution in this city.
Format as numbered list. Be specific and actionable. Max 3 lines each."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Plant trees, use public transport, reduce burning waste."
    
def calculate_carbon(data):
    driving = float(data.get('driving', 0))
    flights = float(data.get('flights', 0))
    electricity = float(data.get('electricity', 0))
    meat = float(data.get('meat', 0))
    
    total = (driving * 0.21) + (flights * 255) + (electricity * 0.4) + (meat * 3.3 * 52)
    
    prompt = f"""You are AirPulse carbon footprint advisor.
User's annual carbon footprint: {total:.1f} kg CO2
- Driving: {driving} km/week
- Flights: {flights} per year  
- Electricity: {electricity} kWh/month
- Meat consumption: {meat} meals/week

Give:
🌍 Carbon Score: {total:.0f} kg CO2/year (compare to world average 4,000 kg)
📊 Breakdown: which activity contributes most
✅ Top 3 actions to reduce footprint significantly
🌱 Equivalent: how many trees needed to offset this

Be specific and motivating."""
    try:
        response = model.generate_content(prompt)
        return {"total": round(total, 1), "advice": response.text}
    except:
        return {"total": round(total, 1), "advice": f"Your footprint is {total:.0f} kg CO2/year."}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>AirPulse - Know What You Breathe</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --bg: #030712;
            --bg2: #0f172a;
            --bg3: #1e293b;
            --text: #f8fafc;
            --text2: #94a3b8;
            --border: rgba(255,255,255,0.08);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
        body::before {
            content: '';
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.12) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 80%, rgba(16,185,129,0.08) 0%, transparent 50%);
            pointer-events: none; z-index: 0;
        }
        nav {
            position: sticky; top: 0; z-index: 1000;
            padding: 16px 40px;
            display: flex; align-items: center; justify-content: space-between;
            background: rgba(3,7,18,0.85);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
        }
        .nav-logo { display: flex; align-items: center; gap: 12px; }
        .nav-logo-icon {
            width: 42px; height: 42px;
            background: linear-gradient(135deg, #10b981, #6366f1);
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.3em;
        }
        .nav-logo h1 {
            font-size: 1.4em; font-weight: 800;
            background: linear-gradient(135deg, #fff, #10b981);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .nav-badge {
            background: rgba(16,185,129,0.15);
            border: 1px solid rgba(16,185,129,0.3);
            color: #10b981; padding: 6px 14px;
            border-radius: 20px; font-size: 0.78em; font-weight: 600;
            display: flex; align-items: center; gap: 6px;
        }
        .live-dot { width: 6px; height: 6px; background: #10b981; border-radius: 50%; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        .hero {
            text-align: center; padding: 80px 20px 50px;
            position: relative; z-index: 1;
        }
        .hero-pill {
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(16,185,129,0.15);
            border: 1px solid rgba(16,185,129,0.35);
            padding: 8px 20px; border-radius: 30px;
            font-size: 0.82em; color: #10b981; margin-bottom: 28px;
        }
        .hero h2 { font-size: 3.5em; font-weight: 900; line-height: 1.1; margin-bottom: 20px; }
        .hero h2 .line1 { display: block; color: #fff; }
        .hero h2 .line2 {
            display: block;
            background: linear-gradient(135deg, #10b981, #6366f1);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .hero-sub { font-size: 1.1em; color: var(--text2); max-width: 500px; margin: 0 auto 40px; line-height: 1.7; }
        .main { max-width: 800px; margin: 0 auto; padding: 0 20px 80px; position: relative; z-index: 1; }
        .search-card {
            background: rgba(15,23,42,0.8);
            border: 1px solid var(--border);
            border-radius: 24px; padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
        }
        .search-bar { display: flex; gap: 12px; margin-bottom: 20px; }
        .search-input {
            flex: 1; padding: 14px 20px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 14px; color: #fff;
            font-size: 1em; font-family: 'Inter', sans-serif;
            outline: none; transition: all 0.2s;
        }
        .search-input:focus { border-color: #10b981; background: rgba(16,185,129,0.08); }
        .search-input::placeholder { color: #475569; }
        .search-btn {
            background: linear-gradient(135deg, #10b981, #6366f1);
            color: white; border: none; padding: 14px 28px;
            border-radius: 14px; cursor: pointer; font-weight: 700;
            font-family: 'Inter', sans-serif; font-size: 1em;
            transition: all 0.2s;
        }
        .search-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16,185,129,0.4); }
        .quick-cities { display: flex; flex-wrap: wrap; gap: 8px; }
        .city-btn {
            background: rgba(99,102,241,0.08);
            border: 1px solid rgba(99,102,241,0.25);
            color: #a78bfa; padding: 8px 16px;
            border-radius: 20px; cursor: pointer;
            font-size: 0.82em; font-family: 'Inter', sans-serif;
            transition: all 0.2s;
        }
        .city-btn:hover { background: rgba(99,102,241,0.2); color: #fff; transform: translateY(-2px); }
        .result-card {
            background: rgba(15,23,42,0.8);
            border: 1px solid var(--border);
            border-radius: 24px; padding: 32px;
            margin-bottom: 24px; display: none;
        }
        .aqi-display { text-align: center; margin-bottom: 28px; }
        .aqi-number { font-size: 5em; font-weight: 900; line-height: 1; }
        .aqi-label { font-size: 1.2em; font-weight: 700; margin-top: 8px; }
        .aqi-city { font-size: 0.9em; color: var(--text2); margin-top: 4px; }
        .pollutants {
            display: grid; grid-template-columns: repeat(3, 1fr);
            gap: 12px; margin-bottom: 28px;
        }
        .pollutant-item {
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 12px; padding: 14px; text-align: center;
        }
        .pollutant-name { font-size: 0.72em; color: var(--text2); margin-bottom: 4px; }
        .pollutant-value { font-size: 1.1em; font-weight: 700; }
        .ai-advice {
            background: rgba(99,102,241,0.08);
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 16px; padding: 24px;
        }
        .ai-advice-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
        .ai-avatar {
            width: 32px; height: 32px;
            background: linear-gradient(135deg, #10b981, #6366f1);
            border-radius: 8px; display: flex; align-items: center; justify-content: center;
        }
        .ai-advice-text { font-size: 0.88em; line-height: 1.8; color: #e2e8f0; }
        .loading { text-align: center; padding: 20px; display: none; }
        .loading-dots { display: inline-flex; gap: 6px; }
        .loading-dots span {
            width: 8px; height: 8px; background: #10b981;
            border-radius: 50%; animation: bounce 1.4s infinite ease-in-out;
        }
        .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
        .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }
        .features { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; margin-top: 40px; }
        .feature-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 16px; padding: 24px; text-align: center;
            transition: all 0.3s;
        }
        .feature-card:hover { border-color: rgba(16,185,129,0.4); transform: translateY(-3px); }
        .feature-icon { font-size: 2em; margin-bottom: 12px; }
        .feature-card h4 { font-size: 0.9em; font-weight: 700; margin-bottom: 6px; }
        .feature-card p { font-size: 0.78em; color: var(--text2); line-height: 1.6; }
        footer {
            text-align: center; padding: 40px 20px;
            border-top: 1px solid var(--border);
            color: #475569; font-size: 0.82em;
            position: relative; z-index: 1;
        }
        @media(max-width:600px) {
            .hero h2 { font-size: 2.2em; }
            .features { grid-template-columns: 1fr; }
            .pollutants { grid-template-columns: repeat(2,1fr); }
            nav { padding: 14px 20px; }
        }
    </style>
</head>
<body>
<nav>
    <div class="nav-logo">
        <div class="nav-logo-icon">🌬️</div>
        <div>
            <h1>AirPulse</h1>
        </div>
    </div>
    <div class="nav-badge"><div class="live-dot"></div> Live Air Data</div>
</nav>

<div class="hero">
    <div class="hero-pill">🌍 Powered by Google Gemini AI • Real-time Global Data</div>
    <h2>
        <span class="line1">Know What You Breathe.</span>
        <span class="line2">Act Before It's Too Late.</span>
    </h2>
    <p class="hero-sub">Real-time air quality data + AI health advice for any city worldwide. Protect yourself and your community.</p>
</div>

<div class="main">
    <div class="search-card">
        <div class="search-bar">
            <input class="search-input" type="text" id="cityInput" 
                placeholder="Enter any city — Delhi, London, New York..." 
                onkeypress="if(event.key==='Enter') checkAir()">
            <button class="search-btn" onclick="checkAir()">Check Air ➤</button>
        </div>
        <div class="quick-cities">
            <button class="city-btn" onclick="quickCheck('delhi')">🇮🇳 Delhi</button>
            <button class="city-btn" onclick="quickCheck('mumbai')">🇮🇳 Mumbai</button>
            <button class="city-btn" onclick="quickCheck('beijing')">🇨🇳 Beijing</button>
            <button class="city-btn" onclick="quickCheck('london')">🇬🇧 London</button>
            <button class="city-btn" onclick="quickCheck('new york')">🇺🇸 New York</button>
            <button class="city-btn" onclick="quickCheck('tokyo')">🇯🇵 Tokyo</button>
            <button class="city-btn" onclick="quickCheck('paris')">🇫🇷 Paris</button>
            <button class="city-btn" onclick="quickCheck('sydney')">🇦🇺 Sydney</button>
        </div>
    </div>

    <div class="loading" id="loading">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <p style="margin-top:12px;color:#94a3b8">Fetching real-time air data + AI analysis...</p>
    </div>

    <div class="result-card" id="resultCard">
        <div class="aqi-display">
            <div class="aqi-number" id="aqiNumber">--</div>
            <div class="aqi-label" id="aqiLabel">--</div>
            <div class="aqi-city" id="aqiCity">--</div>
        </div>
        <div class="pollutants" id="pollutants"></div>
        <div class="ai-advice">
            <div class="ai-advice-header">
                <div class="ai-avatar">🤖</div>
                <div>
                    <strong>AirPulse AI Health Advisor</strong>
                    <div style="font-size:0.72em;color:#10b981">Powered by Google Gemini</div>
                </div>
            </div>
            <div class="ai-advice-text" id="aiAdvice">--</div>
        </div>
    </div>
    
        <!-- ECO TIPS CARD -->
    <div class="result-card" id="ecoCard" style="display:none;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
            <div style="font-size:1.5em;">🌱</div>
            <div>
                <strong style="font-size:1em;">Hyperlocal Eco Tips</strong>
                <div style="font-size:0.72em;color:#10b981">AI tips to reduce pollution in your city</div>
            </div>
        </div>
        <div id="ecoTips" style="font-size:0.88em;line-height:1.8;color:#e2e8f0;"></div>
    </div>

    <!-- CARBON CALCULATOR -->
    <div style="background:rgba(15,23,42,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:24px;padding:32px;margin-bottom:24px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px;">
            <div style="font-size:1.5em;">👣</div>
            <div>
                <strong style="font-size:1em;">Carbon Footprint Calculator</strong>
                <div style="font-size:0.72em;color:#10b981">Calculate your personal CO2 impact</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
            <div>
                <label style="font-size:0.78em;color:#94a3b8;display:block;margin-bottom:6px;">🚗 Driving (km/week)</label>
                <input type="number" id="driving" placeholder="e.g. 100" style="width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#fff;font-family:Inter,sans-serif;outline:none;">
            </div>
            <div>
                <label style="font-size:0.78em;color:#94a3b8;display:block;margin-bottom:6px;">✈️ Flights (per year)</label>
                <input type="number" id="flights" placeholder="e.g. 2" style="width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#fff;font-family:Inter,sans-serif;outline:none;">
            </div>
            <div>
                <label style="font-size:0.78em;color:#94a3b8;display:block;margin-bottom:6px;">⚡ Electricity (kWh/month)</label>
                <input type="number" id="electricity" placeholder="e.g. 200" style="width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#fff;font-family:Inter,sans-serif;outline:none;">
            </div>
            <div>
                <label style="font-size:0.78em;color:#94a3b8;display:block;margin-bottom:6px;">🥩 Meat meals (per week)</label>
                <input type="number" id="meat" placeholder="e.g. 5" style="width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#fff;font-family:Inter,sans-serif;outline:none;">
            </div>
        </div>
        <button onclick="calcCarbon()" style="width:100%;background:linear-gradient(135deg,#10b981,#6366f1);color:white;border:none;padding:14px;border-radius:14px;cursor:pointer;font-weight:700;font-family:Inter,sans-serif;font-size:0.95em;">Calculate My Carbon Footprint ➤</button>
        <div id="carbonResult" style="margin-top:20px;display:none;">
            <div id="carbonScore" style="text-align:center;font-size:2.5em;font-weight:900;color:#10b981;margin-bottom:12px;"></div>
            <div id="carbonAdvice" style="font-size:0.88em;line-height:1.8;color:#e2e8f0;"></div>
        </div>
    </div>

        <div class="features">
        <div class="feature-card">
            <div class="feature-icon">🌍</div>
            <h4>Global Coverage</h4>
            <p>Real-time AQI data for thousands of cities worldwide from verified monitoring stations</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h4>AI Health Advice</h4>
            <p>Google Gemini analyzes your local air quality and gives personalized health recommendations</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🌱</div>
            <h4>Eco Tips</h4>
            <p>AI-generated hyperlocal tips to reduce pollution in your specific city</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">👣</div>
            <h4>Carbon Calculator</h4>
            <p>Calculate your personal carbon footprint and get AI advice to reduce it</p>
        </div>
    </div>
</div>

<footer>
    <strong>AirPulse</strong> — AI-Powered Air Quality Intelligence<br>
    Powered by Google Gemini AI • Real-time data from WAQI<br>
    Built for Earth Forward 🌍 • NextStep Hacks 2026
</footer>

<script>
function quickCheck(city) {
    document.getElementById('cityInput').value = city;
    checkAir();
}

async function checkAir() {
    const city = document.getElementById('cityInput').value.trim();
    if (!city) return;
    
    document.getElementById('loading').style.display = 'block';
    document.getElementById('resultCard').style.display = 'none';
    
    try {
        const response = await fetch('/check', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({city: city})
        });
        const data = await response.json();
        
        if (data.error) {
            alert('City not found. Try another city name.');
            document.getElementById('loading').style.display = 'none';
            return;
        }
        
        document.getElementById('aqiNumber').textContent = data.aqi;
        document.getElementById('aqiNumber').style.color = data.color;
        document.getElementById('aqiLabel').textContent = data.status;
        document.getElementById('aqiLabel').style.color = data.color;
        document.getElementById('aqiCity').textContent = data.city;
        
        let pollutantsHTML = '';
        for (const [key, val] of Object.entries(data.pollutants)) {
            pollutantsHTML += `<div class="pollutant-item">
                <div class="pollutant-name">${key.toUpperCase()}</div>
                <div class="pollutant-value" style="color:${data.color}">${val}</div>
            </div>`;
        }
        document.getElementById('pollutants').innerHTML = pollutantsHTML;
        document.getElementById('aiAdvice').innerHTML = data.advice.replace(/\\n/g, '<br>');
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('resultCard').style.display = 'block';
        document.getElementById('resultCard').scrollIntoView({behavior: 'smooth'});
        
                // Fetch eco tips
        fetch('/eco-tips', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({city: city, aqi: data.aqi})
        }).then(r => r.json()).then(eco => {
            document.getElementById('ecoTips').innerHTML = eco.tips.replace(/\\n/g, '<br>');
            document.getElementById('ecoCard').style.display = 'block';
        });
        
    } catch(e) {
        document.getElementById('loading').style.display = 'none';
        alert('Something went wrong. Please try again.');
    }
}

async function calcCarbon() {
    const driving = document.getElementById('driving').value || 0;
    const flights = document.getElementById('flights').value || 0;
    const electricity = document.getElementById('electricity').value || 0;
    const meat = document.getElementById('meat').value || 0;
    
    try {
        const response = await fetch('/carbon', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({driving, flights, electricity, meat})
        });
        const data = await response.json();
        document.getElementById('carbonScore').textContent = data.total + ' kg CO2/year';
        document.getElementById('carbonAdvice').innerHTML = data.advice.replace(/\\n/g, '<br>');
        document.getElementById('carbonResult').style.display = 'block';
    } catch(e) {
        alert('Something went wrong. Please try again.');
    }
}
</script>
</body>
</html>"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/check', methods=['POST'])
def check_air():
    data = request.json
    city = data.get('city', '')
    
    aqi_data = get_aqi(city)
    if not aqi_data:
        return jsonify({"error": "City not found"})
    
    aqi = aqi_data.get('aqi', 0)
    color, status = get_aqi_color(aqi)
    city_name = aqi_data.get('city', {}).get('name', city)
    
    pollutants = {}
    iaqi = aqi_data.get('iaqi', {})
    for key in ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']:
        if key in iaqi:
            pollutants[key] = iaqi[key]['v']
    
    prompt = f"""You are AirPulse, an AI air quality health advisor.

Current real-time air quality data for {city_name}:
- AQI: {aqi} ({status})
- Pollutants: {pollutants}

Provide a clear, helpful response with exactly these sections:
🏥 Health Risk: (1-2 sentences on current risk level)
👥 Most at Risk: (who should be most careful)
✅ 5 Actions to Stay Safe Today: (numbered list)
⏰ Best Time to Go Outside: (specific advice)
🏭 For Local Businesses: (2-3 tips to reduce environmental impact)

Be practical, caring, and specific. Keep it concise."""

    try:
        response = model.generate_content(prompt)
        advice = response.text
    except Exception as e:
        print(f"GEMINI ERROR: {str(e)}")
        advice = f"AI analysis temporarily unavailable. AQI is {aqi} — {status}."
    
    return jsonify({
        "aqi": aqi,
        "status": status,
        "color": color,
        "city": city_name,
        "pollutants": pollutants,
        "advice": advice
    })

@app.route('/health')
def health():
    return jsonify({"status": "running", "product": "AirPulse", "version": "1.0"})

@app.route('/eco-tips', methods=['POST'])
def eco_tips():
    data = request.json
    city = data.get('city', 'your city')
    aqi = data.get('aqi', 100)
    tips = get_eco_tips(aqi, city)
    return jsonify({"tips": tips})

@app.route('/carbon', methods=['POST'])
def carbon():
    data = request.json
    result = calculate_carbon(data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
