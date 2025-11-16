import numpy as np
import yfinance as yf
from flask import Flask, request, jsonify
from flask_cors import CORS
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import json

app = Flask(__name__)
CORS(app)

# --- Model and Scaler Loading ---
try:
    model = load_model('stock_predictor_model.h5')
    scaler = MinMaxScaler(feature_range=(0, 1))
    sample_data = yf.download('GOOGL', start='2020-01-01', end='2021-01-01')
    # --- THIS LINE IS NOW CORRECTED ---
    sample_close_prices = sample_data['Close'].values.reshape(-1, 1)
    scaler.fit(sample_close_prices)
    print("Model and scaler loaded successfully.")
except Exception as e:
    print(f"FATAL: Error loading model or scaler: {e}")
    model = None
    scaler = None

@app.route('/predict', methods=['POST'])
def predict():
    if not model or not scaler:
        return jsonify({'error': 'Model is not loaded properly. Check server logs.'}), 500

    data = request.get_json(force=True)
    ticker_symbol = data.get('ticker')
    if not ticker_symbol:
        return jsonify({'error': 'Stock ticker symbol not provided.'}), 400

    try:
        ticker_obj = yf.Ticker(ticker_symbol)
        info = ticker_obj.info
        company_name = info.get('longName', 'N/A')

        hist_data = ticker_obj.history(period='1y')
        if hist_data.empty:
            return jsonify({'error': f'No data found for ticker: {ticker_symbol}.'}), 404

        hist_data = hist_data.reset_index()
        ohlc_data = hist_data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict(orient='records')

        close_prices = hist_data['Close'].values.reshape(-1, 1)
        scaled_data = scaler.fit_transform(close_prices)

        time_step = 100
        days_to_predict = 30
        last_sequence = scaled_data[-time_step:]
        temp_input = list(last_sequence.flatten())
        prediction_output = []

        for _ in range(days_to_predict):
            x_input = np.array(temp_input[-time_step:]).reshape((1, time_step, 1))
            yhat = model.predict(x_input, verbose=0)
            temp_input.append(yhat[0][0])
            prediction_output.append(yhat[0][0])

        predicted_prices_scaled = np.array(prediction_output).reshape(-1, 1)
        predicted_prices = scaler.inverse_transform(predicted_prices_scaled)

        return jsonify({
            'ticker': ticker_symbol,
            'company_name': company_name,
            'ohlc_data': ohlc_data,
            'predicted_prices': predicted_prices.flatten().tolist(),
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {json.dumps(str(e))}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)