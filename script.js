document.addEventListener('DOMContentLoaded', () => {
    // --- Get references to our HTML elements ---
    const form = document.getElementById('predict-form');
    const input = document.getElementById('ticker-input');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');
    const chartContainer = document.getElementById('chart-container');
    const mainTitle = document.getElementById('main-title');
    const canvas = document.getElementById('stockChart');
    const companyListNav = document.getElementById('company-list');
    const sidebar = document.getElementById('sidebar');
    const menuOpenBtn = document.getElementById('menu-open-btn');
    const menuCloseBtn = document.getElementById('menu-close-btn');
    let myChart = null;

    const popularCompanies = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 
        'ORCL', 'ADBE', 'CRM', 'INTC', 'AMD', 'QCOM', 'IBM',
        'JPM', 'BAC', 'WFC', 'GS', 'V', 'MA',
        'WMT', 'COST', 'PG', 'KO', 'PEP', 'NKE',
        'JNJ', 'PFE', 'UNH', 'LLY',
        'XOM', 'CVX', 'DIS', 'BA'
    ];

    async function handlePredict(ticker) {
        if (!ticker || typeof ticker !== 'string' || ticker.trim() === '') {
            errorMessage.textContent = 'Please provide a valid stock ticker.';
            errorMessage.classList.remove('hidden');
            chartContainer.classList.add('hidden');
            loadingSpinner.classList.add('hidden');
            return;
        }

        chartContainer.classList.add('hidden');
        errorMessage.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');

        try {
            const response = await fetch('http://127.0.0.1:5000/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker.toUpperCase() }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to fetch prediction.');
            
            displayChart(data);
            updateSidebar(ticker.toUpperCase());
        } catch (err) {
            errorMessage.textContent = err.message;
            errorMessage.classList.remove('hidden');
        } finally {
            loadingSpinner.classList.add('hidden');
        }
    }

    function displayChart(data) {
        chartContainer.classList.remove('hidden');
        mainTitle.textContent = `${data.company_name} (${data.ticker})`;
        
        const ohlcData = data.ohlc_data.map(d => ({ x: new Date(d.Date).getTime(), o: d.Open, h: d.High, l: d.Low, c: d.Close }));
        
        const lastHistoricalPoint = ohlcData[ohlcData.length - 1];
        let lastDate = new Date(lastHistoricalPoint.x);
        const predictionPoints = data.predicted_prices.map(price => {
            lastDate.setDate(lastDate.getDate() + 1);
            return { x: lastDate.getTime(), y: price };
        });

        const connectedPredictionData = [
            { x: lastHistoricalPoint.x, y: lastHistoricalPoint.c },
            ...predictionPoints
        ];

        if (myChart) myChart.destroy();

        myChart = new Chart(canvas, {
            type: 'candlestick',
            data: {
                datasets: [{
                    label: 'Historical Price',
                    data: ohlcData,
                    color: { up: '#22C55E', down: '#EF4444', unchanged: '#9CA3AF' }
                }, {
                    type: 'line',
                    label: 'Predicted Price',
                    data: connectedPredictionData,
                    borderColor: '#F59E0B',
                    borderWidth: 2,
                    pointRadius: 0,
                    borderDash: [5, 5],
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { type: 'time', grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#9CA3AF' } },
                    y: { grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#9CA3AF' } }
                },
                // --- THIS IS THE CRITICAL FIX FOR THE TOOLTIP ---
                plugins: {
                    legend: { labels: { color: '#E5E7EB' } },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                    }
                }
                // The complex callback is not needed if the data is structured correctly.
                // The library will automatically show the correct OHLC details.
                // ---------------------------------------------
            }
        });
    }

    function buildSidebar() {
        popularCompanies.forEach(ticker => {
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = ticker;
            link.className = 'sidebar-link block p-3 rounded-lg cursor-pointer transition-all mb-2 font-semibold hover:bg-gray-700';
            link.dataset.ticker = ticker;
            link.onclick = (e) => {
                e.preventDefault();
                input.value = '';
                handlePredict(ticker);
                sidebar.classList.remove('show');
            };
            companyListNav.appendChild(link);
        });
    }

    function updateSidebar(activeTicker) {
        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.classList.toggle('active', link.dataset.ticker === activeTicker);
        });
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (input.value) handlePredict(input.value);
    });
    
    menuOpenBtn.addEventListener('click', () => sidebar.classList.add('show'));
    menuCloseBtn.addEventListener('click', () => sidebar.classList.remove('show'));

    buildSidebar();
    handlePredict('AAPL');
});