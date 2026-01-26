// Prostock Dashboard Logic

const API_BASE = '/api';

// Initialize Chart
function initChart() {
    const data = [{
        x: [],
        y: [],
        type: 'scatter',
        mode: 'lines',
        name: 'Price',
        line: { color: '#8b5cf6', width: 2, shape: 'spline' },
        fill: 'tozeroy',
        fillcolor: 'rgba(139, 92, 246, 0.05)'
    }];

    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#94a3b8', family: 'Outfit' },
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', showgrid: true },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', showgrid: true },
        margin: { t: 20, r: 20, b: 40, l: 40 },
        hovermode: 'x unified'
    };

    const config = { responsive: true, displayModeBar: false };
    Plotly.newPlot('main-chart', data, layout, config);
}

// Fetch and Update Signals
async function updateSignals() {
    try {
        const response = await fetch(`${API_BASE}/predictions`);
        const data = await response.json();

        const tbody = document.querySelector('#signals-table tbody');
        tbody.innerHTML = `
            <tr>
                <td>${data.symbol}</td>
                <td><span class="badge ${data.signal === 'BUY' ? 'badge-buy' : 'badge-sell'}">${data.signal}</span></td>
                <td>₹${data.price.toFixed(2)}</td>
                <td style="color: #ef4444; font-weight: 700;">₹${data.stop_loss}</td>
                <td style="color: #22c55e; font-weight: 700;">₹${data.target}</td>
                <td><button class="btn-sm active">TRADE</button></td>
            </tr>
        `;

        // Update hero prediction
        document.getElementById('ai-signal').textContent = data.signal === 'BUY' ? 'BULLISH' : 'BEARISH';
        document.getElementById('ai-signal').parentElement.style.background = data.signal === 'BUY' ? 'linear-gradient(135deg, #22c55e, #10b981)' : 'linear-gradient(135deg, #ef4444, #f43f5e)';
    } catch (e) {
        console.error("Error fetching signals", e);
    }
}

async function loadBacktest() {
    try {
        const response = await fetch(`${API_BASE}/backtest`);
        const data = await response.json();

        if (data.status === "error") {
            console.error(data.message);
            return;
        }

        document.getElementById('bt-strategy-return').textContent = `${data.total_return.toFixed(2)}%`;
        document.getElementById('bt-market-return').textContent = `${data.market_return.toFixed(2)}%`;
        document.getElementById('bt-sharpe').textContent = data.sharpe_ratio.toFixed(2);
        document.getElementById('bt-drawdown').textContent = `${data.max_drawdown.toFixed(2)}%`;

        // Color coding
        document.getElementById('bt-strategy-return').style.color = data.total_return >= 0 ? '#22c55e' : '#ef4444';
    } catch (e) {
        console.error("Error loading backtest", e);
    }
}

// Fetch and Update Portfolio
async function updatePortfolio() {
    try {
        const response = await fetch(`${API_BASE}/portfolio`);
        const result = await response.json();

        const rows = result.data.map(item => `
            <tr>
                <td>${item.symbol}</td>
                <td>${item.qty}</td>
                <td>₹${item.avg_price}</td>
                <td style="color: ${item.pnl >= 0 ? '#22c55e' : '#ef4444'}">
                    ₹${item.pnl.toFixed(2)}
                </td>
            </tr>
        `).join('');

        // Populate Dashboard Table
        const miniTable = document.querySelector('#portfolio-table tbody');
        if (miniTable) miniTable.innerHTML = rows;

        // Populate Dedicated Table
        const dedicatedTable = document.querySelector('#portfolio-table-dedicated tbody');
        if (dedicatedTable) dedicatedTable.innerHTML = rows;

    } catch (e) {
        console.error("Error fetching portfolio", e);
    }
}

// Fetch and Update Orders
async function updateOrders() {
    try {
        const response = await fetch(`${API_BASE}/orders`);
        const result = await response.json();

        const tbody = document.querySelector('#orders-table tbody');
        if (!tbody) return;

        tbody.innerHTML = result.map(order => `
            <tr>
                <td>${order.order_id}</td>
                <td>${order.symbol}</td>
                <td><span class="badge ${order.side === 'BUY' ? 'badge-buy' : 'badge-sell'}">${order.side}</span></td>
                <td>${order.status}</td>
                <td>${order.qty || '--'}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error("Error fetching orders", e);
    }
}

// Mock chart update
let timeCount = 0;
function simulateLiveChart() {
    const time = new Date();
    const price = 21000 + Math.random() * 100;

    Plotly.extendTraces('main-chart', {
        x: [[time]],
        y: [[price]]
    }, [0]);

    if (timeCount > 50) {
        Plotly.relayout('main-chart', {
            xaxis: {
                range: [new Date(time.getTime() - 50 * 1000), time]
            }
        });
    }
    timeCount++;
}

// Search Logic
async function handleSearch(query) {
    if (!query) return;
    try {
        const response = await fetch(`${API_BASE}/search?query=${query}`);
        const result = await response.json();
        if (result.results && result.results.length > 0) {
            // In a real app, this might switch the chart view
            console.log(`Found symbol: ${result.results[0]}`);
            alert(`Focusing on ${result.results[0]}`);
        }
    } catch (e) {
        console.error("Search failed", e);
    }
}

// Tab Switching Logic
function initTabs() {
    const navItems = document.querySelectorAll('.sidebar nav li');

    navItems.forEach((item, index) => {
        item.addEventListener('click', () => {
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            const viewName = item.textContent.trim().toLowerCase();
            showView(viewName);
        });
    });
}

// Broker Switching Logic
async function handleBrokerSwitch(broker) {
    try {
        const response = await fetch(`${API_BASE}/config/switch?broker=${broker}`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.status === "success") {
            updateUIWithConfig(result.active_broker);
            updateProfile(); // Refresh profile for new broker
        }
    } catch (e) {
        console.error("Error switching broker", e);
    }
}

async function updateUIWithConfig(activeBroker) {
    const display = document.getElementById('active-broker-display');
    const selector = document.getElementById('broker-selector');

    const name = activeBroker === 'indstocks' ? 'Indstocks' : 'Kotak Neo';
    display.textContent = `${name} Connected`;
    if (selector) selector.value = activeBroker;
}

async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        const config = await response.json();
        updateUIWithConfig(config.active_broker);
    } catch (e) {
        console.error("Error loading config", e);
    }
}

function showView(name) {
    const views = document.querySelectorAll('.tab-content');
    views.forEach(v => v.classList.remove('active'));

    if (name.includes('dashboard')) document.getElementById('dashboard-view').classList.add('active');
    else if (name.includes('portfolio')) document.getElementById('portfolio-view').classList.add('active');
    else if (name.includes('orders')) document.getElementById('orders-view').classList.add('active');
    else if (name.includes('models')) document.getElementById('models-view').classList.add('active');
    else if (name.includes('settings')) document.getElementById('settings-view').classList.add('active');
}

// Fetch and Update User Profile from Indstocks
async function updateProfile() {
    try {
        const response = await fetch(`${API_BASE}/profile`);
        const result = await response.json();

        if (result.status === "success") {
            const user = result.data;
            // Update profile section if we have a name/id field
            console.log(`Connected to Indstocks as ${user.first_name}`);
            // You could update a name label in header if present
        }
    } catch (e) {
        console.error("Error fetching profile", e);
    }
}

// Live Clock Logic
function refreshClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-IN', { hour12: false });
    const dateStr = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
    document.getElementById('live-clock').textContent = `${dateStr} | ${timeStr}`;
}

// Fetch Real Live Data for all Indices
async function updateLiveMetrics() {
    try {
        // 1. Update Index Cards & Status
        const indexResponse = await fetch(`${API_BASE}/indices`);
        const result = await indexResponse.json();

        if (result.status === "error") {
            console.warn("Index API Error:", result.message);
            return;
        }

        // Update Market Status Badge
        const statusObj = result.market;
        if (statusObj) {
            const statusBadge = document.getElementById('market-status-badge');
            statusBadge.textContent = statusObj.status.toUpperCase();
            statusBadge.className = `market-status ${statusObj.open ? 'open' : 'closed'}`;
        }

        const cardMap = {
            "NIFTY 50": 1,
            "BANKNIFTY": 2,
            "SENSEX": 3
        };

        for (const [name, data] of Object.entries(result)) {
            if (name === "market") continue;

            const cardIdx = cardMap[name];
            if (cardIdx) {
                const card = document.querySelector(`.metrics-grid .metric-card:nth-child(${cardIdx})`);
                card.querySelector('.metric-value').textContent = `₹${data.price.toFixed(2)}`;
                const changeEl = card.querySelector('.metric-change');
                changeEl.textContent = `${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)} (${data.change_pct.toFixed(2)}%)`;
                changeEl.className = `metric-change ${data.change >= 0 ? 'positive' : 'negative'}`;
            }
        }

        // 2. Update Main Chart (using Nifty as default)
        if (result["NIFTY 50"]) {
            const time = new Date();
            Plotly.extendTraces('main-chart', {
                x: [[time]],
                y: [[result["NIFTY 50"].price]]
            }, [0]);
        }

    } catch (e) {
        console.error("Error updating live metrics", e);
    }
}

// Global Init
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    initTabs();
    loadConfig();
    updateSignals();
    updatePortfolio();
    updateOrders();
    updateProfile();
    loadBacktest();
    refreshClock();

    // Refresh loop
    setInterval(refreshClock, 1000); // Live Clock
    setInterval(updateSignals, 10000); // AI Prediction refresh
    setInterval(updateLiveMetrics, 2000); // Live index refresh (including BankNifty/Sensex)
    setInterval(updatePortfolio, 30000);
    setInterval(updateOrders, 30000);
});
