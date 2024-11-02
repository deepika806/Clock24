from flask import Flask, render_template_string, request
from datetime import datetime
import pytz

app = Flask(__name__)

# List of timezones with display names for the dropdown
timezones = {
    "UTC": "UTC",
    "US/Eastern": "USA (Eastern)",
    "US/Central": "USA (Central)",
    "US/Pacific": "USA (Pacific)",
    "Europe/London": "UK (London)",
    "Europe/Berlin": "Germany (Berlin)",
    "Asia/Tokyo": "Japan (Tokyo)",
    "Asia/Kolkata": "India (Kolkata)",
    "Australia/Sydney": "Australia (Sydney)",
}

# HTML template with enhanced styles and interactivity
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Clock & Stopwatch</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-image: url('static/modern-style-frame-red-line-presentation-dark-background-vector.png'); /* Change this to your image URL */
            background-size: cover; /* Cover the entire viewport */
            background-position: center; /* Center the background image */
            font-family: 'Roboto', sans-serif;
            color: #00FFFF;
        }
        .main-container {
            display: flex;
            gap: 20px;
            align-items: flex-start;
            flex-wrap: wrap;
        }
        .container, .left-container {
            background-color: rgba(0, 0, 0, 0.7);
            border: 3px solid #00FFFF;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            height: 650px;
            width: 550px;
            max-width: 90vw;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .container:hover, .left-container:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 40px rgba(0, 0, 0, 0.7);
        }
        .container {
            text-align: center;
            font-size: 22px;
        }
        .left-container {
            color: #FFF;
            font-size: 24px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        .analog-clock {
            position: relative;
            width: 300px; /* Increased width */
            height: 300px; /* Increased height */
            background-color: rgba(255, 255, 255, 0.2);
            border: 5px solid #00FFFF;
            border-radius: 15px;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            margin-top: 20px; /* Added margin */
        }
        .hand {
            position: absolute;
            background: #00FFFF;
            transform-origin: bottom;
            border-radius: 5px;
        }
        .hour-hand {
            height: 70px;
            width: 6px;
            z-index: 3;
        }
        .minute-hand {
            height: 100px;
            width: 4px;
            z-index: 2;
        }
        .second-hand {
            height: 120px;
            width: 2px;
            background: red;
            z-index: 1;
        }
        .header {
            display: flex;
            justify-content: space-around;
            padding-bottom: 10px;
            border-bottom: 3px solid #00FFFF;
            margin-bottom: 20px;
        }
        .header div {
            cursor: pointer;
            padding: 15px;
            font-size: 22px;
            transition: color 0.3s;
        }
        .header div:hover {
            color: #FFF;
            text-shadow: 0 0 10px #00FFFF;
        }
        .header div.active {
            font-weight: bold;
            color: #00FFFF;
        }
        .date, .clock, .stopwatch, .worldclock {
            font-size: 50px;
            margin: 20px 0;
        }
        .date {
            font-size: 28px;
        }
        select, button {
            margin: 5px;
            padding: 15px 25px;
            font-size: 18px;
            background-color: #00FFFF;
            color: black;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        select:hover, button:hover {
            background-color: #007B7F;
        }
    </style>
</head>
<body>

<div class="main-container">
    <div class="left-container">
        <h2>Analog Clock</h2>
        <div class="analog-clock" id="analogClock">
            <div class="hand hour-hand" id="hourHand"></div>
            <div class="hand minute-hand" id="minuteHand"></div>
            <div class="hand second-hand" id="secondHand"></div>
        </div>
    </div>
    <div class="container">
        <div class="header">
            <div id="tab12" class="active" onclick="showTab('12hour')">12-hour Clock</div>
            <div id="tab24" onclick="showTab('24hour')">24-hour Clock</div>
            <div id="tabStopwatch" onclick="showTab('stopwatch')">Stopwatch</div>
            <div id="tabWorldClock" onclick="showTab('worldclock')">World Clock</div>
        </div>

        <div class="date" id="date">{{ date }}</div>
        <div class="clock" id="clock">{{ time }}</div>

        <div id="worldclockContainer" style="display:none;">
            <select id="timezoneSelect" onchange="updateWorldClock()">
                {% for tz, name in timezones.items() %}
                    <option value="{{ tz }}">{{ name }}</option>
                {% endfor %}
            </select>
            <div class="worldclock" id="worldclock">Select a timezone</div>
        </div>

        <div class="stopwatch" id="stopwatch" style="display:none;">00:00:00</div>
        <div id="stopwatchControls" style="display:none;">
            <button onclick="startStopwatch()">Start</button>
            <button onclick="stopStopwatch()">Stop</button>
            <button onclick="resetStopwatch()">Reset</button>
        </div>
    </div>
</div>

<script>
    let is24HourFormat = false;
    let activeTab = '12hour';
    let stopwatchInterval;
    let stopwatchTime = 0; // Time in seconds
    let isStopwatchRunning = false;

    function updateTime() {
        fetch('/time?format=' + (is24HourFormat ? '24' : '12'))
            .then(response => response.json())
            .then(data => {
                document.getElementById('clock').textContent = data.time;
                document.getElementById('date').textContent = data.date;
            });
    }

    function updateWorldClock() {
        const timezone = document.getElementById('timezoneSelect').value;
        fetch('/worldclock?timezone=' + timezone)
            .then(response => response.json())
            .then(data => {
                document.getElementById('worldclock').textContent = data.time;
            });
    }

    function updateAnalogClock() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const seconds = now.getSeconds();
        
        const hourDeg = (hours % 12) * 30 + (minutes / 60) * 30;
        const minuteDeg = (minutes + seconds / 60) * 6;
        const secondDeg = seconds * 6;

        document.getElementById('hourHand').style.transform = `rotate(${hourDeg}deg)`;
        document.getElementById('minuteHand').style.transform = `rotate(${minuteDeg}deg)`;
        document.getElementById('secondHand').style.transform = `rotate(${secondDeg}deg)`;
    }

    function startStopwatch() {
        if (!isStopwatchRunning) {
            isStopwatchRunning = true;
            stopwatchInterval = setInterval(() => {
                stopwatchTime++;
                const hours = Math.floor(stopwatchTime / 3600);
                const minutes = Math.floor((stopwatchTime % 3600) / 60);
                const seconds = stopwatchTime % 60;
                document.getElementById('stopwatch').textContent = 
                    String(hours).padStart(2, '0') + ':' +
                    String(minutes).padStart(2, '0') + ':' +
                    String(seconds).padStart(2, '0');
            }, 1000);
        }
    }

    function stopStopwatch() {
        isStopwatchRunning = false;
        clearInterval(stopwatchInterval);
    }

    function resetStopwatch() {
        stopStopwatch();
        stopwatchTime = 0;
        document.getElementById('stopwatch').textContent = '00:00:00';
    }

    function showTab(tab) {
        document.getElementById('tab12').classList.remove('active');
        document.getElementById('tab24').classList.remove('active');
        document.getElementById('tabStopwatch').classList.remove('active');
        document.getElementById('tabWorldClock').classList.remove('active');

        document.getElementById('clock').style.display = 'block';
        document.getElementById('stopwatch').style.display = 'none';
        document.getElementById('stopwatchControls').style.display = 'none';
        document.getElementById('worldclockContainer').style.display = 'none';

        if (tab === '12hour') {
            document.getElementById('tab12').classList.add('active');
            is24HourFormat = false;
            updateTime();
        } else if (tab === '24hour') {
            document.getElementById('tab24').classList.add('active');
            is24HourFormat = true;
            updateTime();
        } else if (tab === 'stopwatch') {
            document.getElementById('tabStopwatch').classList.add('active');
            document.getElementById('stopwatchControls').style.display = 'block';
            document.getElementById('stopwatch').style.display = 'block';
        } else if (tab === 'worldclock') {
            document.getElementById('tabWorldClock').classList.add('active');
            document.getElementById('worldclockContainer').style.display = 'block';
        }
    }

    setInterval(updateTime, 1000);
    setInterval(updateAnalogClock, 1000);
</script>

</body>
</html>
"""

@app.route('/')
def index():
    current_time = datetime.now()
    date = current_time.strftime("%A, %B %d, %Y")
    time = current_time.strftime("%I:%M:%S %p")
    return render_template_string(html_template, date=date, time=time, timezones=timezones)

@app.route('/time')
def time():
    format = request.args.get('format', '12')
    now = datetime.now()
    date = now.strftime("%A, %B %d, %Y")
    if format == '24':
        time = now.strftime("%H:%M:%S")
    else:
        time = now.strftime("%I:%M:%S %p")
    return {"date": date, "time": time}

@app.route('/worldclock')
def worldclock():
    timezone = request.args.get('timezone', 'UTC')
    now = datetime.now(pytz.timezone(timezone))
    time = now.strftime("%I:%M:%S %p")
    return {"time": time}

if __name__ == '__main__':
    app.run(debug=True)
