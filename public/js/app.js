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
  // Fade out, then update text, fade in
  elem.classList.add('fade-updating');
  setTimeout(() => {
    elem.textContent = newValue;
    elem.classList.remove('fade-updating');
  }, 300);
}

// Fade update for entire <ol>
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

// Fade update for a table <tbody>
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

    // Current conditions
    const currentDetails = timeseries[0].data.instant.details;

    // Temperature
    const tempC = currentDetails.air_temperature.toFixed(1);
    smoothTextUpdate(document.getElementById('temperature'), `${tempC} °C`);

    // Hidden #wind-speed
    smoothTextUpdate(
      document.getElementById('wind-speed'),
      `${currentDetails.wind_speed.toFixed(1)} m/s`
    );

    // Compass speed
    smoothTextUpdate(
      document.getElementById('wind-speed-value'),
      `${currentDetails.wind_speed.toFixed(1)} m/s`
    );

    // Rotate arrow
    const windDir = currentDetails.wind_from_direction;
    document.getElementById('wind-arrow').style.transform = `rotate(${windDir}deg)`;

    buildForecastTable(timeseries);

  } catch (error) {
    console.error('Error fetching weather:', error);
  }
}

function setSymbolImage(imgId, symbolCode) {
  const imgElem = document.getElementById(imgId);
  if (!imgElem) return;

  if (!symbolCode) {
    imgElem.src = 'images/weathericons/svg/clearsky_day.svg';
    return;
  }
  let base = symbolCode
    .replace('_day','')
    .replace('_night','')
    .replace('_polartwilight','');

  imgElem.src = `images/weathericons/svg/${base}.svg`;
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
    // "today"
    if (data.today && data.today.prices) {
      const todayAvg = data.today.average;
      smoothTextUpdate(
        document.getElementById('avg-price-today'),
        todayAvg != null && !isNaN(todayAvg) ? todayAvg.toFixed(1) : '--'
      );

      const todayLabels = [];
      const todayValues = [];
      let currentPriceValue = null;
      const now = new Date();
      const currentHour = now.getHours();

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

    // "tomorrow"
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
  if (canvasId === 'priceChart' && priceChart) {
    priceChart.destroy();
  } else if (canvasId === 'priceChartTomorrow' && priceChartTomorrow) {
    priceChartTomorrow.destroy();
  }
  const ctx = document.getElementById(canvasId).getContext('2d');
  const chartConfig = {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'øre/kWh',
        data: prices,
        backgroundColor: prices.map((p, i) => {
          if (currentHour !== null && i === currentHour) {
            return 'rgba(255, 99, 132, 0.8)'; // highlight current hour
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

    // Pressure
    smoothTextUpdate(
      document.getElementById('enzv-pressure'),
      current.altim_hpa != null ? current.altim_hpa.toFixed(1) : '--'
    );
    // Temp
    smoothTextUpdate(
      document.getElementById('enzv-temp'),
      current.temp_c != null ? current.temp_c.toFixed(1) : '--'
    );
    // Dew
    smoothTextUpdate(
      document.getElementById('enzv-dew'),
      current.dewpoint_c != null ? current.dewpoint_c.toFixed(1) : '--'
    );
    // Vis
    smoothTextUpdate(
      document.getElementById('enzv-vis'),
      current.visibility_statute_mi != null
        ? current.visibility_statute_mi.toFixed(1)
        : '--'
    );

    // Wind
    let windStr = '--';
    if (current.wind_dir_deg != null && current.wind_speed_kt != null) {
      windStr = `${Math.round(current.wind_dir_deg)}° @ ${Math.round(current.wind_speed_kt)} kt`;
    }
    smoothTextUpdate(document.getElementById('enzv-wind'), windStr);

    // Trend arrow
    const arrowEl = document.getElementById('enzv-trend-arrow');
    arrowEl.classList.remove('bi-arrow-up', 'bi-arrow-down', 'bi-dash');
    if (trend === 'up') arrowEl.classList.add('bi-arrow-up');
    else if (trend === 'down') arrowEl.classList.add('bi-arrow-down');
    else arrowEl.classList.add('bi-dash');

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
  if (enzvChart) enzvChart.destroy();
  enzvChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Pressure (hPa)',
        data: values,
        borderColor: 'rgba(99,132,255,1)',
        backgroundColor: 'rgba(99,132,255,0.2)',
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: false,
          title: { display: true, text: 'hPa' }
        }
      },
      plugins: { legend: { display: false } }
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

      // METAR text
      const textElem = document.getElementById(`metar-${icao}`);
      if (textElem) {
        smoothTextUpdate(textElem, m.rawOb || '--');
      }
      // flight rule dot
      const fr = classifyFlightRules(m);
      const dotElem = document.getElementById(`dot-${icao}`);
      if (dotElem) {
        dotElem.style.backgroundColor = fr.color;
      }
      // wind icon
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

// 8A) Distances for "on ground"
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
  const distNm = distKm / 1.852;
  return distNm;
}
function isOnGround(pilot, airport) {
  if (!pilot.latitude || !pilot.longitude) return false;
  const dist = distanceNm(airport.lat, airport.lon, pilot.latitude, pilot.longitude);
  if (dist > 5) return false; // outside 5 nm
  // also check speed or altitude
  if (pilot.groundspeed && pilot.groundspeed < 50) return true;
  if (pilot.altitude && pilot.altitude < 2000) return true;
  return false;
}

// 8B) Aircraft families
const aircraftFamilyMap = {
  A32: "Airbus A320",
  A33: "Airbus A330",
  A34: "Airbus A340",
  A35: "Airbus A350",
  A38: "Airbus A380",
  B73: "Boeing 737",
  B74: "Boeing 747",
  B75: "Boeing 757",
  B76: "Boeing 767",
  B77: "Boeing 777",
  B78: "Boeing 787",
  CRJ: "Bombardier CRJ",
  E17: "Embraer 170-175",
  E19: "Embraer 190-195"
};
function getAircraftFamily(acftShort) {
  if (!acftShort || acftShort.length < 3) return acftShort || "Unknown";
  const prefix = acftShort.substring(0,3).toUpperCase();
  return aircraftFamilyMap[prefix] || prefix;
}

// 8C) Tracked "Favorite" airports
const trackedAirports = [
  { icao: "ENGM", name: "Oslo Gardermoen",    lat: 60.202,  lon: 11.083 },
  { icao: "ENZV", name: "Stavanger Sola",     lat: 58.8765, lon: 5.637 },
  { icao: "KJFK", name: "New York JFK",       lat: 40.6398, lon: -73.7789 },
  { icao: "KEWR", name: "Newark Liberty EWR",     lat: 40.6925, lon: -74.1687 },
  { icao: "KLGA", name: "New York LaGuardia",    lat: 40.7772, lon: -73.8726 },
  { icao: "KPHL", name: "Philadelphia PHL",      lat: 39.8719, lon: -75.2411 },
  { icao: "KLAX", name: "Los Angeles LAX",       lat: 33.9425, lon: -118.4081 }
];

const VATSIM_DATA_URL = 'https://data.vatsim.net/v3/vatsim-data.json';

// 8D) Main fetch for VATSIM Stats
async function fetchVatsimStats() {
  const statusElem = document.getElementById('vatsim-status');

  // Summary table
  const summaryTbody  = document.querySelector('#vatsim-summary-table tbody');
  // Most popular airports
  const airportsTbody = document.querySelector('#vatsim-airports-table tbody');
  // Most popular aircraft
  const aircraftTbody = document.querySelector('#vatsim-aircraft-table tbody');
  // Favorite airports
  const trackedTbody  = document.querySelector('#vatsim-airport-table tbody');

  smoothTextUpdate(statusElem, 'Loading...');
  try {
    const resp = await fetch(VATSIM_DATA_URL);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    const data = await resp.json();

    // Summaries
    const totalClients = data.general.connected_clients || 0;
    const totalPilots  = data.pilots ? data.pilots.length : 0;
    const totalAtc     = data.controllers ? data.controllers.length : 0;

    smoothTextUpdate(statusElem, 'Data updated');

    ////////////////////////////
    // 1) VATSIM Summary Table
    ////////////////////////////
    const summaryRows = [
      `<tr><td>Total Clients</td><td>${totalClients}</td></tr>`,
      `<tr><td>Pilots</td><td>${totalPilots}</td></tr>`,
      `<tr><td>Controllers</td><td>${totalAtc}</td></tr>`
    ];
    smoothTableUpdate(summaryTbody, summaryRows);

    ////////////////////////////
    // 2) Most Popular Airports
    ////////////////////////////
    const depMap = {};
    data.pilots.forEach(p => {
      const dep = p.flight_plan?.departure;
      if (dep) {
        const apt = dep.toUpperCase();
        depMap[apt] = (depMap[apt] || 0) + 1;
      }
    });
    const sortedApts = Object.entries(depMap)
      .sort((a,b) => b[1] - a[1])
      .slice(0,5);

    const airportRows = sortedApts.map(([apt, count]) =>
      `<tr><td>${apt}</td><td>${count}</td></tr>`
    );
    smoothTableUpdate(airportsTbody, airportRows);

    ////////////////////////////
    // 3) Most Popular Aircraft
    ////////////////////////////
    const acftMap = {};
    data.pilots.forEach(p => {
      const short = p.flight_plan?.aircraft_short;
      if (!short) return;
      const fam = getAircraftFamily(short);
      acftMap[fam] = (acftMap[fam] || 0) + 1;
    });
    const sortedAcft = Object.entries(acftMap)
      .sort((a,b) => b[1] - a[1])
      .slice(0,5);

    const aircraftRows = sortedAcft.map(([fam, c]) =>
      `<tr><td>${fam}</td><td>${c}</td></tr>`
    );
    smoothTableUpdate(aircraftTbody, aircraftRows);

    ////////////////////////////
    // 4) Favorite Airports
    ////////////////////////////
    const stats = {};
    trackedAirports.forEach(a => {
      stats[a.icao] = { icao:a.icao, name:a.name, departures:0, arrivals:0, onGround:0 };
    });

    data.pilots.forEach(pilot => {
      const dep = pilot.flight_plan?.departure?.toUpperCase() || "";
      const arr = pilot.flight_plan?.arrival?.toUpperCase() || "";

      if (stats[dep]) stats[dep].departures++;
      if (stats[arr]) stats[arr].arrivals++;

      trackedAirports.forEach(apt => {
        if (isOnGround(pilot, apt)) {
          stats[apt.icao].onGround++;
        }
      });
    });

    const favRows = trackedAirports.map(a => {
      const s = stats[a.icao];
      return `
        <tr>
          <td>${s.icao}</td>
          <td>${s.departures}</td>
          <td>${s.arrivals}</td>
          <td>${s.onGround}</td>
        </tr>
      `;
    });
    smoothTableUpdate(trackedTbody, favRows);

  } catch (err) {
    console.error('Error fetching VATSIM stats:', err);
    smoothTextUpdate(statusElem, `Error: ${err.message}`);
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