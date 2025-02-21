// ==========================
// 1. Update the clock (24h)
// ==========================
function updateTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');
  document.getElementById('time').textContent = `${hh}:${mm}:${ss}`;
}
setInterval(updateTime, 1000);
updateTime();

// ==========================
// Smooth text fade helper
// ==========================
function smoothTextUpdate(elem, newValue) {
  elem.classList.add('fade-updating');
  setTimeout(() => {
    elem.textContent = newValue;
    elem.classList.remove('fade-updating');
  }, 300);
}

function smoothListUpdate(listElem, items) {
  listElem.classList.add('fade-updating');
  setTimeout(() => {
    listElem.innerHTML = '';
    items.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      listElem.appendChild(li);
    });
    listElem.classList.remove('fade-updating');
  }, 300);
}

function smoothTableUpdate(tbodyElem, rowHtmlArray) {
  tbodyElem.classList.add('fade-updating');
  setTimeout(() => {
    tbodyElem.innerHTML = rowHtmlArray.join('');
    tbodyElem.classList.remove('fade-updating');
  }, 300);
}

// ==========================
// 2) Current Weather, symbols
// ==========================
async function fetchCurrentWeather() {
  try {
    const res = await fetch('/api/weather');
    const data = await res.json();

    setSymbolImage('symbol-1h', data.symbol_1h);
    setSymbolImage('symbol-6h', data.symbol_6h);
    setSymbolImage('symbol-12h', data.symbol_12h);

    const timeseries = data.properties?.timeseries;
    if (!timeseries || timeseries.length === 0) {
      console.error('No timeseries data from /api/weather');
      return;
    }

    const currentDetails = timeseries[0].data.instant.details;
    const tempC = currentDetails.air_temperature.toFixed(1);
    smoothTextUpdate(document.getElementById('temperature'), `${tempC} °C`);

    smoothTextUpdate(
        document.getElementById('wind-speed'),
        `${currentDetails.wind_speed.toFixed(1)} m/s`
    );

    smoothTextUpdate(
        document.getElementById('wind-speed-value'),
        `${currentDetails.wind_speed.toFixed(1)} m/s`
    );

    const windDir = currentDetails.wind_from_direction;
    document.getElementById('wind-arrow').style.transform = `rotate(${windDir}deg)`;

    buildForecastTable(timeseries);

  } catch (error) {
    console.error('Error fetching weather:', error);
  }
}

/**
 * setSymbolImage
 * @param {string} imgId - The DOM id of the <img> element to update.
 * @param {string} symbolCode - The base symbol code from met.no (e.g. "clearsky_day").
 * @param {string} dateStr - The date in "YYYY-MM-DD" format (defaults to today).
 */
async function setSymbolImage(imgId, symbolCode, dateStr) {
  const imgElem = document.getElementById(imgId);
  if (!imgElem) return;

  // If symbolCode is blank, default to clearsky
  if (!symbolCode) {
    imgElem.src = 'images/weathericons/svg/clearsky_day.svg';
    return;
  }

  // Normalize the "base" symbol by removing day/night/polartwilight
  const base = symbolCode
      .replace('_day', '')
      .replace('_night', '')
      .replace('_polartwilight', '');

  // 1) Fetch sunrise/sunset data
  //    (If dateStr is missing, you might default to today's date.)
  const today = dateStr || new Date().toISOString().slice(0, 10);
  let sunData;
  try {
    const res = await fetch(`/api/sun?date=${today}`);
    sunData = await res.json();
  } catch (err) {
    console.error("Error fetching /api/sun data:", err);
    // Fallback to base icon if fetch fails
    imgElem.src = `images/weathericons/svg/${base}.svg`;
    return;
  }

  // 2) Extract sunrise/sunset from sunData
  //    Check for validity in case "No local data" was returned
  const sunriseStr = sunData?.properties?.sunrise?.time;
  const sunsetStr  = sunData?.properties?.sunset?.time;
  if (!sunriseStr || !sunsetStr) {
    // No sunrise/sunset data found, just default to base
    imgElem.src = `images/weathericons/svg/${base}.svg`;
    return;
  }

  const sunriseTime = new Date(sunriseStr);
  const sunsetTime  = new Date(sunsetStr);
  const now         = new Date();

  // 3) Decide if it's day or night
  //    (Simple check: day if now between sunrise & sunset, else night)
  const isDaytime = (now >= sunriseTime && now < sunsetTime);

  // 4) Attempt a "day" or "night" icon
  const dayOrNight = isDaytime ? 'day' : 'night';
  const candidateIcon = `images/weathericons/svg/${base}_${dayOrNight}.svg`;

  // 5) Check if the candidate icon actually exists
  //    We'll do a HEAD request: if response.ok => it exists
  let iconExists = false;
  try {
    const headRes = await fetch(candidateIcon, { method: 'HEAD' });
    iconExists = headRes.ok;  // true if the file is found
  } catch (error) {
    // If an error occurs (e.g. network error), just treat as if it doesn't exist
    console.warn("HEAD request failed for", candidateIcon, error);
  }

  // 6) Pick final path based on existence
  const finalIconPath = iconExists
      ? candidateIcon
      : `images/weathericons/svg/${base}.svg`;

  // 7) Set <img> src
  imgElem.src = finalIconPath;
}

function buildForecastTable(timeseries) {
  const forecastBody = document.getElementById('forecast-table').querySelector('tbody');
  forecastBody.innerHTML = '';
  const limit = 12;
  for (let i = 0; i < limit && i < timeseries.length; i++) {
    const ts = timeseries[i];
    const instant = ts.data.instant.details;
    const dt = new Date(ts.time);
    const hh = String(dt.getHours()).padStart(2, '0');
    const mm = String(dt.getMinutes()).padStart(2, '0');
    const timeStr = `${hh}:${mm}`;

    const t = instant.air_temperature.toFixed(1);
    const w = instant.wind_speed.toFixed(1);

    let precip = 0;
    if (ts.data.next_1_hours && ts.data.next_1_hours.details) {
      precip = ts.data.next_1_hours.details.precipitation_amount || 0;
    } else if (ts.data.next_6_hours && ts.data.next_6_hours.details) {
      precip = ts.data.next_6_hours.details.precipitation_amount || 0;
    }

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${timeStr}</td>
      <td>${t}</td>
      <td>${w}</td>
      <td>${precip.toFixed(1)}</td>
    `;
    forecastBody.appendChild(row);
  }
}

// ==========================
// 3. Sunrise/Sunset
// ==========================
let todayDaylightMinutes = null;

async function fetchSunTimes() {
  try {
    const res = await fetch('/api/sun');
    const data = await res.json();
    if (data.type !== 'Feature') {
      console.error('Sun data not Feature:', data);
      return;
    }
    const srISO = data.properties?.sunrise?.time;
    const ssISO = data.properties?.sunset?.time;

    if (srISO) {
      const srDate = new Date(srISO);
      const srStr = srDate.toLocaleTimeString([], {
        hour: '2-digit', minute: '2-digit', hour12: false
      });
      smoothTextUpdate(document.getElementById('sunrise'), srStr);
    }
    if (ssISO) {
      const ssDate = new Date(ssISO);
      const ssStr = ssDate.toLocaleTimeString([], {
        hour: '2-digit', minute: '2-digit', hour12: false
      });
      smoothTextUpdate(document.getElementById('sunset'), ssStr);
    }

    todayDaylightMinutes = getDaylightDurationMinutes(srISO, ssISO);
    smoothTextUpdate(
        document.getElementById('today-length'),
        formatHoursMinutes(todayDaylightMinutes)
    );
  } catch (err) {
    console.error('Error fetching sunrise:', err);
  }
}

function getDaylightDurationMinutes(sunrise, sunset) {
  if (!sunrise || !sunset) return 0;
  const sr = new Date(sunrise);
  const ss = new Date(sunset);
  return Math.round((ss - sr) / 60000);
}
function formatHoursMinutes(totalMins) {
  const hrs = Math.floor(totalMins / 60);
  const mins = totalMins % 60;
  return `${hrs}h ${mins}m`;
}
function formatDiff(diff) {
  const sign = diff > 0 ? '+' : '';
  return `(${sign}${diff} min)`;
}

async function compareSunTimes() {
  if (todayDaylightMinutes === null) {
    await fetchSunTimes();
  }
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  const inOneWeek = new Date();
  inOneWeek.setDate(inOneWeek.getDate() + 7);

  const now = new Date();
  let dec21Year = now.getFullYear();
  if (now.getMonth() === 0) dec21Year -= 1;
  const dec21Str = `${dec21Year}-12-21`;

  const [weekAgoData, inOneWeekData, dec21Data] = await Promise.all([
    fetchSunriseForDate(toIsoDateString(oneWeekAgo)),
    fetchSunriseForDate(toIsoDateString(inOneWeek)),
    fetchSunriseForDate(dec21Str)
  ]);

  const weekAgoMins = weekAgoData?.minutes ?? 0;
  const inOneWeekMins = inOneWeekData?.minutes ?? 0;
  const dec21Mins = dec21Data?.minutes ?? 0;

  const diffWeekAgo = weekAgoMins - todayDaylightMinutes;
  const diffInWeek = inOneWeekMins - todayDaylightMinutes;
  const diffDec21 = dec21Mins - todayDaylightMinutes;

  smoothTextUpdate(
      document.getElementById('week-compare'),
      `${formatHoursMinutes(weekAgoMins)} ${formatDiff(diffWeekAgo)}`
  );
  smoothTextUpdate(
      document.getElementById('inweek-compare'),
      `${formatHoursMinutes(inOneWeekMins)} ${formatDiff(diffInWeek)}`
  );
  smoothTextUpdate(
      document.getElementById('shortest-compare'),
      `${formatHoursMinutes(dec21Mins)} ${formatDiff(diffDec21)}`
  );
}

async function fetchSunriseForDate(dateStr) {
  try {
    const resp = await fetch(`/api/sun?date=${dateStr}`);
    const data = await resp.json();
    if (data.type !== 'Feature') return null;
    const srISO = data.properties?.sunrise?.time;
    const ssISO = data.properties?.sunset?.time;
    const mins = getDaylightDurationMinutes(srISO, ssISO);
    return { minutes: mins };
  } catch (err) {
    console.error('Error fetch sunrise for', dateStr, err);
    return null;
  }
}
function toIsoDateString(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// 5) Electricity Prices
let priceChart = null;
let priceChartTomorrow = null;
async function fetchPrices() {
  try {
    const res = await fetch('/api/prices');
    const data = await res.json();
    const now = new Date();
    const currentHour = now.getHours();

    if (data.today && data.today.prices) {
      const todayAvg = data.today.average;
      smoothTextUpdate(
          document.getElementById('avg-price-today'),
          todayAvg != null && !isNaN(todayAvg) ? todayAvg.toFixed(1) : '--'
      );

      const todayLabels = [];
      const todayValues = [];
      let currentPriceValue = null;

      data.today.prices.forEach(item => {
        const startDate = new Date(item.time_start);
        if (isNaN(startDate)) return;
        const hour = startDate.getHours();
        todayLabels.push(`${hour}:00`);

        const ore = parseFloat(item.NOK_per_kWh) * 100;
        todayValues.push(ore);
        if (hour === currentHour) {
          currentPriceValue = ore;
        }
      });

      if (currentPriceValue !== null && !isNaN(currentPriceValue)) {
        smoothTextUpdate(
            document.getElementById('current-price'),
            currentPriceValue.toFixed(0)
        );
      } else {
        smoothTextUpdate(document.getElementById('current-price'), '--');
      }

      createPriceChart('priceChart', todayLabels, todayValues, currentHour);
    }

    if (data.tomorrow && data.tomorrow.prices) {
      document.getElementById('tomorrowAverageRow').style.display = 'block';
      const tomAvg = data.tomorrow.average;
      smoothTextUpdate(
          document.getElementById('avg-price-tomorrow'),
          tomAvg != null && !isNaN(tomAvg) ? tomAvg.toFixed(1) : '--'
      );

      const tomorrowChartDiv = document.getElementById('tomorrowChartContainer');
      tomorrowChartDiv.style.display = 'block';

      const tLabels = [];
      const tValues = [];
      data.tomorrow.prices.forEach(item => {
        const startDate = new Date(item.time_start);
        if (isNaN(startDate)) return;
        const hour = startDate.getHours();
        tLabels.push(`${hour}:00`);
        const ore = parseFloat(item.NOK_per_kWh) * 100;
        tValues.push(ore);
      });
      createPriceChart('priceChartTomorrow', tLabels, tValues, null);
    }
  } catch (err) {
    console.error('Error fetching prices:', err);
  }
}

function createPriceChart(canvasId, labels, prices, currentHour) {
  const ctx = document.getElementById(canvasId).getContext('2d');

  // Destroy existing chart before creating a new one
  if (canvasId === 'priceChart' && priceChart) {
    priceChart.destroy();
  } else if (canvasId === 'priceChartTomorrow' && priceChartTomorrow) {
    priceChartTomorrow.destroy();
  }

  const chartConfig = {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'øre/kWh',
        data: prices,
        backgroundColor: prices.map((p, i) => {
          if (currentHour !== null && i === currentHour) {
            return 'rgba(255, 99, 132, 0.8)'; // Highlight current hour in red
          }
          return 'rgba(99, 132, 255, 0.6)';
        }),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'øre/kWh' }
        }
      },
      plugins: { legend: { display: false } }
    }
  };

  // Create the new chart instance
  if (canvasId === 'priceChart') {
    priceChart = new Chart(ctx, chartConfig);
  } else {
    priceChartTomorrow = new Chart(ctx, chartConfig);
  }
}

// 6) ENZV
async function fetchEnzvData() {
  try {
    const res = await fetch('/api/enzv');
    const data = await res.json();
    if (data.error) {
      console.error('ENZV error:', data.error);
      return;
    }
    const { current, history, trend } = data;

    // 1) Update pressure, temp, wind, visibility
    let pressureStr = '--';
    if (current.altim_hpa != null && current.altim_in_hg != null) {
      pressureStr = `${current.altim_hpa.toFixed(1)} hPa - ${current.altim_in_hg.toFixed(2)} inHg`;
    } else if (current.altim_hpa != null) {
      pressureStr = `${current.altim_hpa.toFixed(1)} hPa`;
    }
    smoothTextUpdate(document.getElementById('enzv-pressure'), pressureStr);

    smoothTextUpdate(
        document.getElementById('enzv-temp'),
        current.temp_c != null ? current.temp_c.toFixed(1) : '--'
    );
    smoothTextUpdate(
        document.getElementById('enzv-dew'),
        current.dewpoint_c != null ? current.dewpoint_c.toFixed(1) : '--'
    );
    smoothTextUpdate(
        document.getElementById('enzv-vis'),
        current.visibility_statute_mi != null
            ? current.visibility_statute_mi.toFixed(1)
            : '--'
    );

    let windStr = '--';
    if (current.wind_dir_deg != null && current.wind_speed_kt != null) {
      windStr = `${Math.round(current.wind_dir_deg)}° @ ${Math.round(current.wind_speed_kt)} kt`;
    }
    smoothTextUpdate(document.getElementById('enzv-wind'), windStr);

    // 2) Update trend arrow
    const arrowEl = document.getElementById('enzv-trend-arrow');
    arrowEl.classList.remove('bi-arrow-up', 'bi-arrow-down', 'bi-dash');
    if (trend === 'up') arrowEl.classList.add('bi-arrow-up');
    else if (trend === 'down') arrowEl.classList.add('bi-arrow-down');
    else arrowEl.classList.add('bi-dash');

    // 3) Update the pressure chart dynamically
    buildEnzvPressureChart(history);

  } catch (err) {
    console.error('Error fetching /api/enzv:', err);
  }
}

let enzvChart = null;
function buildEnzvPressureChart(history) {
  const labels = [];
  const values = [];
  history.forEach(pt => {
    const dt = new Date(pt.time);
    const hh = String(dt.getHours()).padStart(2, '0');
    const mm = String(dt.getMinutes()).padStart(2, '0');
    labels.push(`${hh}:${mm}`);
    values.push(pt.altim_hpa);
  });

  const ctx = document.getElementById('enzvPressureChart').getContext('2d');
  if (enzvChart) enzvChart.destroy(); // if you re-create the chart frequently

  enzvChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Pressure (hPa)',
        data: values,
        borderColor: 'rgba(99, 132, 255, 1)',
        backgroundColor: 'rgba(99, 132, 255, 0.2)',
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      // Add "elements.line.tension" or "cubicInterpolationMode"
      elements: {
        line: {
          tension: 0.6 // smooth the curve
          // OR cubicInterpolationMode: 'monotone'
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          title: { display: true, text: 'hPa' },
          // Force tick labels to be whole numbers
          ticks: {
            callback: function(value) {
              return Math.round(value);
            }
          }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// 7) METAR
async function fetchMetars() {
  try {
    const res = await fetch('/api/metars');
    const data = await res.json();

    data.forEach(m => {
      const icao = m.icaoId?.toLowerCase();
      if (!icao) return;

      const textElem = document.getElementById(`metar-${icao}`);
      if (textElem) {
        smoothTextUpdate(textElem, m.rawOb || '--');
      }

      const fr = classifyFlightRules(m);
      const dotElem = document.getElementById(`dot-${icao}`);
      if (dotElem) {
        dotElem.style.backgroundColor = fr.color;
      }

      const wspd = m.wspd || 0;
      const windIconElem = document.getElementById(`wind-${icao}`);
      if (windIconElem) {
        windIconElem.textContent = '';
        windIconElem.innerHTML = '';
        windIconElem.style.color = '';
        if (wspd > 40) {
          windIconElem.textContent = '!';
          windIconElem.style.color = 'red';
        } else if (wspd > 25) {
          windIconElem.innerHTML = `<i class="bi bi-wind"></i>`;
          windIconElem.style.color = 'lightblue';
        }
      }
    });
  } catch (err) {
    console.error('Error fetching METARs:', err);
  }
}
// 1) Define your list of airports.
const airportList = ["ENZV", "ENGM", "KJFK", "KLAX", "KORD", "TNCM", "EGLL", "RJAA"];

// 2) Get the container from the DOM
const metarContainer = document.getElementById("metar-container");

// 3) For each airport, create the same row structure
airportList.forEach(icao => {
  // Create a <div> with the same layout
  const rowDiv = document.createElement('div');
  rowDiv.style.display = 'flex';
  rowDiv.style.alignItems = 'baseline';

  // Create the flight-rule dot
  const dotSpan = document.createElement('span');
  dotSpan.className = 'flight-rule-dot fade';
  dotSpan.id = `dot-${icao.toLowerCase()}`;

  // Create the wind icon span
  const windSpan = document.createElement('span');
  windSpan.className = 'wind-icon fade';
  windSpan.id = `wind-${icao.toLowerCase()}`;
  windSpan.style.marginRight = '0.5em';

  // Create the code element
  const codeElem = document.createElement('code');
  codeElem.className = 'fade';
  codeElem.id = `metar-${icao.toLowerCase()}`;
  codeElem.style.margin = '0';
  codeElem.style.padding = '0';

  // Append them all inside rowDiv
  rowDiv.appendChild(dotSpan);
  rowDiv.appendChild(windSpan);
  rowDiv.appendChild(codeElem);

  // Finally, append rowDiv into the container
  metarContainer.appendChild(rowDiv);
});

function classifyFlightRules(m) {
  let lowestBase = 99999;
  if (Array.isArray(m.clouds)) {
    m.clouds.forEach(c => {
      if (typeof c.base === 'number' && c.base < lowestBase) {
        lowestBase = c.base;
      }
    });
  }
  let visNum = 10;
  if (m.visib != null) {
    let rawVis = (typeof m.visib === 'string') ? m.visib : String(m.visib);
    rawVis = rawVis.replace('+','');
    const parsed = parseFloat(rawVis);
    if (!isNaN(parsed)) {
      visNum = parsed;
    }
  }
  let category = 'VFR';
  let color = 'green';
  if (lowestBase < 500 || visNum < 1) {
    category = 'LIFR';
    color = 'orange';
  } else if (lowestBase < 1000 || visNum < 3) {
    category = 'IFR';
    color = 'red';
  } else if (lowestBase < 3000 || visNum < 5) {
    category = 'MVFR';
    color = 'blue';
  }
  return { category, color };
}

// =========== 8) VATSIM Section with 4 tables ===========

// 8A) Distances for "on ground" check
function distanceNm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in km
  const toRad = Math.PI / 180;
  const dLat = (lat2 - lat1) * toRad;
  const dLon = (lon2 - lon1) * toRad;
  const a = Math.sin(dLat/2)**2 +
      Math.cos(lat1*toRad)*Math.cos(lat2*toRad)*
      Math.sin(dLon/2)**2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distKm = R * c;
  return distKm / 1.852; // nm
}
function isOnGround(pilot, airport) {
  if (!pilot.latitude || !pilot.longitude) return false;
  const dist = distanceNm(airport.lat, airport.lon, pilot.latitude, pilot.longitude);
  if (dist > 5) return false; // outside 5 nm
  if (pilot.groundspeed && pilot.groundspeed < 50) return true;
  if (pilot.altitude && pilot.altitude < 2000) return true;
  return false;
}

// 8B) Aircraft families
const aircraftFamilyMap = {
  // ========== AIRBUS ==========
  "A318": "Airbus A320",
  "A319": "Airbus A320",
  "A320": "Airbus A320",
  "A321": "Airbus A320",
  "A20N": "Airbus A320neo",
  "A21N": "Airbus A320neo",

  "A330": "Airbus A330",
  "A332": "Airbus A330",
  "A333": "Airbus A330",
  "A338": "Airbus A330neo",
  "A339": "Airbus A330neo",

  "A340": "Airbus A340",
  "A342": "Airbus A340",
  "A343": "Airbus A340",
  "A345": "Airbus A340",
  "A346": "Airbus A340",

  "A350": "Airbus A350",
  "A359": "Airbus A350",
  "A35K": "Airbus A350",

  "A380": "Airbus A380",

  // ========== BOEING ==========
  "B707": "Boeing 707",
  "B717": "Boeing 717",
  "B727": "Boeing 727",

  "B737": "Boeing 737",
  "B731": "Boeing 737",
  "B732": "Boeing 737",
  "B733": "Boeing 737",
  "B734": "Boeing 737",
  "B735": "Boeing 737",
  "B736": "Boeing 737",
  "B737": "Boeing 737",
  "B738": "Boeing 737",
  "B739": "Boeing 737",
  "B37M": "Boeing 737 MAX",
  "B38M": "Boeing 737 MAX",
  "B39M": "Boeing 737 MAX",

  "B747": "Boeing 747",
  "B741": "Boeing 747",
  "B742": "Boeing 747",
  "B743": "Boeing 747",
  "B744": "Boeing 747",
  "B748": "Boeing 747",

  "B757": "Boeing 757",
  "B752": "Boeing 757",
  "B753": "Boeing 757",

  "B767": "Boeing 767",
  "B762": "Boeing 767",
  "B763": "Boeing 767",
  "B764": "Boeing 767",

  "B777": "Boeing 777",
  "B772": "Boeing 777",
  "B773": "Boeing 777",
  "B77L": "Boeing 777",
  "B77W": "Boeing 777",

  "B787": "Boeing 787",
  "B788": "Boeing 787",
  "B789": "Boeing 787",
  "B78X": "Boeing 787",

  // ========== EMBRAER ==========
  "E170": "Embraer E-Jet",
  "E175": "Embraer E-Jet",
  "E190": "Embraer E-Jet",
  "E195": "Embraer E-Jet",
  "E290": "Embraer E2",
  "E295": "Embraer E2",

  // ========== BOMBARDIER ==========
  "CRJ": "Bombardier CRJ",
  "CRJ1": "Bombardier CRJ",
  "CRJ2": "Bombardier CRJ",
  "CRJ7": "Bombardier CRJ",
  "CRJ9": "Bombardier CRJ",
  "CRJX": "Bombardier CRJ",

  "DH8A": "Bombardier Dash 8",
  "DH8B": "Bombardier Dash 8",
  "DH8C": "Bombardier Dash 8",
  "DH8D": "Bombardier Dash 8",

  // ========== ATR ==========
  "AT42": "ATR 42",
  "AT43": "ATR 42",
  "AT45": "ATR 42",
  "AT46": "ATR 42",
  "AT72": "ATR 72",

  // ========== MISC ==========
  "CONC": "Concorde",
  "C130": "Lockheed C-130",
  "L101": "Lockheed L-1011 Tristar",
  "MD11": "McDonnell Douglas MD-11",
  "MD80": "McDonnell Douglas MD-80",
  "MD81": "McDonnell Douglas MD-80",
  "MD82": "McDonnell Douglas MD-80",
  "MD83": "McDonnell Douglas MD-80",
  "MD87": "McDonnell Douglas MD-80",
  "MD88": "McDonnell Douglas MD-80",
  "MD90": "McDonnell Douglas MD-80",

  // ========== COMAC ==========
  "C919": "COMAC C919",
  "ARJ2": "COMAC ARJ21"
};

function getAircraftFamily(acftShort) {
  if (!acftShort || acftShort.length < 3) return acftShort || "Unknown";

  const code = acftShort.toUpperCase();

  // First, check for an exact ICAO match
  if (aircraftFamilyMap[code]) return aircraftFamilyMap[code];

  // If not found, check based on the first 3 letters
  const prefix = code.substring(0, 3);
  return aircraftFamilyMap[prefix] || prefix;
}

// 8C) Tracked "Favorite" airports
const trackedAirports = [
  { icao: "ENGM", name: "Oslo Gardermoen",    lat: 60.202,  lon: 11.083 },
  { icao: "ENZV", name: "Stavanger Sola",     lat: 58.8765, lon: 5.637 },
  { icao: "KJFK", name: "New York JFK",       lat: 40.6398, lon: -73.7789 },
  { icao: "KEWR", name: "Newark Liberty EWR", lat: 40.6925, lon: -74.1687 },
  { icao: "KLGA", name: "New York LaGuardia", lat: 40.7772, lon: -73.8726 },
  { icao: "KPHL", name: "Philadelphia PHL",   lat: 39.8719, lon: -75.2411 },
  { icao: "KLAX", name: "Los Angeles LAX",    lat: 33.9425, lon: -118.4081 }
];

const VATSIM_DATA_URL = 'https://data.vatsim.net/v3/vatsim-data.json';
const MY_VATSIM_CID = 908962;

async function fetchVatsimStats() {
  const myCard = document.getElementById('my-vatsim-card');
  const myCallsignEl = document.getElementById('my-callsign');
  const myAltEl = document.getElementById('my-altitude');
  const myDistEl = document.getElementById('my-dist-remaining');
  const myETEEl = document.getElementById('my-ete');

  // VATSIM Stats elements
  const totalClientsEl = document.getElementById("vatsim-total-clients");
  const totalPilotsEl = document.getElementById("vatsim-total-pilots");
  const totalAtcEl = document.getElementById("vatsim-total-atc");

  const airportsListEl = document.getElementById("vatsim-airports-list");
  const aircraftListEl = document.getElementById("vatsim-aircraft-list");
  const favoriteAirportsEl = document.getElementById("vatsim-favorite-airports");

  if (!myCard || !myCallsignEl || !myAltEl || !myDistEl || !myETEEl) {
    console.error("VATSIM status elements are missing from the DOM.");
    return;
  }

  try {
    const resp = await fetch(VATSIM_DATA_URL);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    console.log(`[VATSIM Stats] Updated at ${new Date().toLocaleTimeString()}`);

    // Extract global stats
    const totalClients = data.general.connected_clients || 0;
    const totalPilots = data.pilots?.length || 0;
    const totalAtc = data.controllers?.length || 0;

    // Update VATSIM Summary Stats
    smoothTextUpdate(totalClientsEl, totalClients);
    smoothTextUpdate(totalPilotsEl, totalPilots);
    smoothTextUpdate(totalAtcEl, totalAtc);

    // === Process Most Popular Airports ===
    const depMap = {};
    data.pilots.forEach(p => {
      const dep = p.flight_plan?.departure;
      if (dep) {
        const apt = dep.toUpperCase().trim();
        depMap[apt] = (depMap[apt] || 0) + 1;
      }
    });
    // === Process Most Popular Airports (Departures, Arrivals, On-Ground) ===
// === Process Most Popular Airports (Departures, Arrivals, On-Ground) ===
const airportStats = {};

// Collect departures, arrivals, and on-ground aircraft counts
data.pilots.forEach(pilot => {
  const dep = pilot.flight_plan?.departure?.toUpperCase().trim();
  const arr = pilot.flight_plan?.arrival?.toUpperCase().trim();
  const lat = pilot.latitude;
  const lon = pilot.longitude;

  if (dep) {
    if (!airportStats[dep]) airportStats[dep] = { departures: 0, arrivals: 0, onGround: 0 };
    airportStats[dep].departures++;
  }

  if (arr) {
    if (!airportStats[arr]) airportStats[arr] = { departures: 0, arrivals: 0, onGround: 0 };
    airportStats[arr].arrivals++;
  }

    // Initialize onGround counter for each airport
  if (dep && !airportStats[dep]) airportStats[dep] = { departures: 0, arrivals: 0, onGround: 0 };
  if (arr && !airportStats[arr]) airportStats[arr] = { departures: 0, arrivals: 0, onGround: 0 };

  // Increase departure and arrival counts
  if (dep) airportStats[dep].departures++;
  if (arr) airportStats[arr].arrivals++;

  // Track on-ground aircraft for each airport separately
  trackedAirports.forEach(airport => {
    if (isOnGround(pilot, airport)) {
      if (!airportStats[airport.icao]) {
        airportStats[airport.icao] = { departures: 0, arrivals: 0, onGround: 0 };
      }
      airportStats[airport.icao].onGround++;
    }
  });
});

// Sort by total departures (descending) and take the top 5
const sortedApts = Object.entries(airportStats)
  .sort((a, b) => b[1].departures - a[1].departures)
  .slice(0, 5);

// Update UI with properly formatted data
airportsListEl.innerHTML = sortedApts.length
  ? sortedApts.map(([icao, stats]) => `
      <div class="airport-bubble">
        <strong>${icao}</strong>
        <span>D: ${stats.departures || 0}</span>
        <span>A: ${stats.arrivals || 0}</span>
        <span>On Ground: ${stats.onGround || 0}</span>
      </div>`).join("")
  : `<div class="loading-text">No data available</div>`;

    // === Process Most Popular Aircraft ===
    const acftMap = {};
    data.pilots.forEach(p => {
      const short = p.flight_plan?.aircraft_short;
      if (!short) return;
      const fam = getAircraftFamily(short);
      acftMap[fam] = (acftMap[fam] || 0) + 1;
    });
    const sortedAcft = Object.entries(acftMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    aircraftListEl.innerHTML = sortedAcft.length
      ? sortedAcft.map(([fam, count]) => `
          <div class="aircraft-bubble">
            <strong>${fam}</strong>
            <span>${count} Flights</span>
          </div>`).join("")
      : `<div class="loading-text">No data available</div>`;

    // === Process Favorite Airports ===
    const stats = {};
    trackedAirports.forEach(a => {
      stats[a.icao] = { icao: a.icao, name: a.name, departures: 0, arrivals: 0, onGround: 0 };
    });

    data.pilots.forEach(pilot => {
      const dep = pilot.flight_plan?.departure?.toUpperCase().trim() || "";
      const arr = pilot.flight_plan?.arrival?.toUpperCase().trim() || "";
      if (stats[dep]) stats[dep].departures++;
      if (stats[arr]) stats[arr].arrivals++;
      trackedAirports.forEach(apt => {
        if (isOnGround(pilot, apt)) stats[apt.icao].onGround++;
      });
    });

    favoriteAirportsEl.innerHTML = trackedAirports.length
      ? trackedAirports.map(a => {
          const s = stats[a.icao];
          return `
            <div class="airport-bubble">
              <strong>${s.icao}</strong>
              <span>${s.departures} / ${s.arrivals} (${s.onGround})</span>
            </div>`;
        }).join("")
      : `<div class="loading-text">No data available</div>`;

    // === Fetch My Personal VATSIM Data ===
    const myPilot = data.pilots.find(p => p.cid === MY_VATSIM_CID);
    if (!myPilot) {
      myCard.style.display = 'none';
      return;
    }
    myCard.style.display = 'block';

    updateVatsimTracker(myPilot);

    // Distance & ETE Updates
    if (myPilot.flight_plan?.arrival !== '--' && myPilot.latitude && myPilot.longitude) {
      const depKey = myPilot.flight_plan.departure?.toUpperCase();
      const arrKey = myPilot.flight_plan.arrival?.toUpperCase();
      const pilotLat = myPilot.latitude;
      const pilotLon = myPilot.longitude;

      const arrDistancePromise = fetch(`/api/distance?icao=${arrKey}&lat=${pilotLat}&lon=${pilotLon}`).then(r => r.json());
      const depDistancePromise = fetch(`/api/distance?icao=${depKey}&lat=${pilotLat}&lon=${pilotLon}`).then(r => r.json());

      Promise.all([arrDistancePromise, depDistancePromise])
        .then(([arrDistData, depDistData]) => {
          if (arrDistData.error || depDistData.error) {
            console.warn('Distance error:', arrDistData.error || depDistData.error);
            return;
          }

          myPilot.distance_from_dep = depDistData.distanceNm;
          myPilot.distance_remaining = arrDistData.distanceNm;
          myPilot.total_distance = myPilot.distance_from_dep + myPilot.distance_remaining;

          if (myPilot.groundspeed > 0 && myPilot.distance_remaining > 1) {
            const hours = myPilot.distance_remaining / myPilot.groundspeed;
            myPilot.ete = `${Math.floor(hours)}h ${Math.floor((hours - Math.floor(hours)) * 60)}m`;
          } else {
            myPilot.ete = "--";
          }

          updateDistanceProgress(myPilot.distance_from_dep, myPilot.total_distance);
          updateVatsimTracker(myPilot);
        })
        .catch(err => console.error('Distance fetch failed', err));
    } else {
      myPilot.distance_from_dep = "--";
      myPilot.distance_remaining = "--";
      myPilot.total_distance = "--";
      myPilot.ete = "--";
      updateVatsimTracker(myPilot);
    }
  } catch (err) {
    console.error('Error fetching VATSIM stats:', err);
    myCard.style.display = 'none';
  }
}

// ----- Helper: Display Aircraft Details in the Detailed Aircraft Card -----
function showMyAircraftRegBox(acData) {
  function updateDetailBox(rowId, value) {
    const row = document.getElementById(rowId);
    if (row) {
      if (value && value.toString().trim() !== "" && value !== "--") {
        row.querySelector("span, pre").textContent = value;
        row.style.display = "block"; // Show only if data exists
      } else {
        row.style.display = "none"; // Hide if missing
      }
    }
  }

  updateDetailBox('row-reg-registration', acData.registration);
  updateDetailBox('row-reg-icao24', acData.icao24);
  updateDetailBox('row-reg-selcal', acData.selcal);
  updateDetailBox('row-reg-type', acData.type || acData.ac_type);
  updateDetailBox('row-reg-operator', acData.operator?.name);
  updateDetailBox('row-reg-model', acData.model);
  updateDetailBox('row-reg-name', acData.name);
  updateDetailBox('row-reg-engines', acData.aircraft_type?.engines);
  updateDetailBox('row-reg-remarks', Array.isArray(acData.remarks) ? acData.remarks.join("\n") : acData.remarks);

  // Handle Aircraft Status Icon
  const statusIcon = document.getElementById("reg-status-icon");
  const status = acData.status ? acData.status.toLowerCase() : "unknown";

  const statusClasses = {
    "active": "status-active",
    "inactive": "status-inactive",
    "stored": "status-stored",
    "retired": "status-retired",
    "scrapped": "status-scrapped"
  };

  // Remove any previous status class
  statusIcon.className = "bi bi-circle-fill status-icon";

  if (statusClasses[status]) {
    statusIcon.classList.add(statusClasses[status]);
    statusIcon.setAttribute("title", status.charAt(0).toUpperCase() + status.slice(1)); // Tooltip text
  } else {
    statusIcon.setAttribute("title", "Unknown");
  }

  // Show card if any details exist
  const regCard = document.getElementById("my-aircraft-reg-card");
  regCard.style.display = Object.values(acData).some(val => val) ? "block" : "none";
}

// ----- Helper: Update the Progress Bar -----
function updateDistanceProgress(distanceFromDep, totalDistance) {
  if (!totalDistance || totalDistance <= 0) return;

  // Correct formula: Calculate progress from departure
  const progressPercent = Math.max(0, Math.min(100, (distanceFromDep / totalDistance) * 100));

  const progressBar = document.getElementById('distance-progress-bar');
  if (progressBar) {
    progressBar.style.width = progressPercent + '%';
  }
}

function getFlightPhase(altitude, vspeed) {
  if (vspeed > 500) return "Climbing";
  if (vspeed < -500) return "Descending";
  if (altitude > 20000) return "Cruising";
  return "Level Flight";
}


function updateVatsimTracker(myPilot) {
  // Set callsign
  smoothTextUpdate(document.getElementById("my-callsign"), myPilot.callsign || "--");

  // Update origin and destination
  smoothTextUpdate(document.getElementById("my-dep"), myPilot.flight_plan?.departure || "--");
  smoothTextUpdate(document.getElementById("my-dest"), myPilot.flight_plan?.arrival || "--");

  // Update flight phase
  const phase = getFlightPhase(myPilot.altitude || 0, myPilot.vertical_speed || 0);
  smoothTextUpdate(document.getElementById("my-phase"), phase);

  // Ensure distance values exist before calling toFixed()
  const distFromOrigin = myPilot.distance_from_dep !== undefined ? myPilot.distance_from_dep.toFixed(0) : "--";
  const totalDist = myPilot.total_distance !== undefined ? myPilot.total_distance.toFixed(0) : "--";
  const distRemaining = myPilot.distance_remaining !== undefined ? myPilot.distance_remaining.toFixed(0) : "--";
  const ete = myPilot.ete || "--";

  smoothTextUpdate(document.getElementById("my-dist-from-origin"), distFromOrigin);
  smoothTextUpdate(document.getElementById("my-total-dist"), totalDist);
  smoothTextUpdate(document.getElementById("my-dist-remaining"), distRemaining);
  smoothTextUpdate(document.getElementById("my-ete"), ete);

  // Update flight details safely
  smoothTextUpdate(document.getElementById("my-altitude"), myPilot.altitude !== undefined ? myPilot.altitude : "--");
  smoothTextUpdate(document.getElementById("my-groundspeed"), myPilot.groundspeed !== undefined ? myPilot.groundspeed : "--");
  smoothTextUpdate(document.getElementById("my-heading"), myPilot.heading !== undefined ? myPilot.heading : "--");
  smoothTextUpdate(document.getElementById("my-vs"), myPilot.vertical_speed !== undefined ? myPilot.vertical_speed : "--");
  smoothTextUpdate(document.getElementById("my-aircraft"), myPilot.flight_plan?.aircraft_short || "--");

  // Update progress bar only if distance values exist
  if (myPilot.distance_from_dep !== undefined && myPilot.total_distance !== undefined) {
    updateDistanceProgress(myPilot.distance_from_dep, myPilot.total_distance);
  }

  // --- Fetch Aircraft Details for Display ---
  const aircraftRegCard = document.getElementById("my-aircraft-reg-card");
  if (myPilot.flight_plan?.remarks) {
    const regMatch = myPilot.flight_plan.remarks.match(/REG\/([A-Za-z0-9\-]+)/i);
    if (regMatch) {
      const foundReg = regMatch[1].toUpperCase();
      fetch(`/api/aircraft/${foundReg}`)
        .then(r => {
          if (!r.ok) throw new Error(`Aircraft not found: ${r.status}`);
          return r.json();
        })
        .then(acData => {
          showMyAircraftRegBox(acData);
          aircraftRegCard.style.display = "block";
        })
        .catch(err => {
          console.warn("No aircraft details for", foundReg, err);
          aircraftRegCard.style.display = "none";
        });
    } else {
      aircraftRegCard.style.display = "none";
    }
  } else {
    aircraftRegCard.style.display = "none";
  }
}

// ==========================
// On Page Load
// ==========================
updateTime();
fetchCurrentWeather();
fetchSunTimes().then(compareSunTimes);
fetchPrices();
fetchEnzvData();
fetchMetars();
fetchVatsimStats();

// Refresh VATSIM every 60 seconds
setInterval(fetchVatsimStats, 60000);
setInterval(fetchCurrentWeather, 300000)
setInterval(fetchPrices, 300000);

// Refresh airport weather data every 5 minutes
setInterval(fetchEnzvData, 300000);

// Refresh METARs every 5 minutes
setInterval(fetchMetars, 300000);