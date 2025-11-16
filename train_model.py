import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
import os

# --- 1. Settings and Configuration ---
STOCK_TICKER = 'GOOGL'  # Ticker symbol for the stock (e.g., Google)
START_DATE = '2015-01-01'
END_DATE = '2025-01-01' # Use up-to-date data
TIME_STEP = 100  # Number of past days' data to use for predicting the next day
MODEL_FILENAME = 'stock_predictor_model.h5'

print(f"Starting model training for {STOCK_TICKER} from {START_DATE} to {END_DATE}")

# --- 2. Data Fetching and Preprocessing ---
print("Fetching stock data...")
df = yf.download(STOCK_TICKER, start=START_DATE, end=END_DATE)

if df.empty:
    print(f"No data fetched for {STOCK_TICKER}. Exiting.")
    exit()

df_close = df.reset_index()['Close']

print("Preprocessing data...")
scaler = MinMaxScaler(feature_range=(0, 1))
df_close_scaled = scaler.fit_transform(np.array(df_close).reshape(-1, 1))

# --- 3. Splitting Data into Training and Testing Sets ---
training_size = int(len(df_close_scaled) * 0.80)
train_data, test_data = df_close_scaled[0:training_size, :], df_close_scaled[training_size:len(df_close_scaled), :1]

def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset) - time_step - 1):
        a = dataset[i:(i + time_step), 0]
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)

X_train, y_train = create_dataset(train_data, TIME_STEP)
X_test, y_test = create_dataset(test_data, TIME_STEP)

X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

# --- 4. Building the LSTM Model ---
print("Building a robust LSTM model...")
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(TIME_STEP, 1)))
model.add(Dropout(0.2))
model.add(LSTM(50, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(50))
model.add(Dropout(0.2))
model.add(Dense(1))

model.compile(loss='mean_squared_error', optimizer='adam')
model.summary()

# --- 5. Training the Model ---
print("Training the model... This may take a several minutes.")
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=50, batch_size=64, verbose=1)

# --- 6. Saving the Model ---
print(f"Saving the trained model to {MODEL_FILENAME}...")
model.save(MODEL_FILENAME)

print("Model training complete and saved successfully!")