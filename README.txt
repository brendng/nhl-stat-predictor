NHL STATLINE PREDICTOR - By Brendan Ng
======================
Last Updated: January 17, 2026

This project predicts the next game's statline for an NHL player using an LSTM model trained on NHL
game data from the 2024-2025 season.

Backend:   Node.js/Express server
Frontend:  React (Vite)
Model:     PyTorch LSTM
Data:      NHL API data

Setup Instructions
==================

1. FETCH DATA
   Open terminal and run from project root:
   
   python fetch_data.py
   
   This will:
   - Download game logs for the 2024-2025 season from the NHL API
   - Extract player statistics and team data
   - Generate player_id_mapping.json with player info
   - Save raw data to data/raw/nhl_game_logs_20242025.csv
   
   (Optional: Run scripts/upgrade_player_names_simple.py to fetch full player names
    if player_id_mapping.json has short names)

2. PREPROCESS DATA
   python preprocess.py
   
   This will:
   - Calculate rolling averages for player stats
   - Add team and opponent context to each game
   - Save processed data to data/processed/nhl_game_logs_processed_20242025.csv

3. TRAIN MODEL
   python train.py
   
   This will:
   - Load the processed dataset and train the LSTM model
   - Display loss and mean absolute error per stat
   - Save the trained model to models/lstm_model.pth
   
   Note: Training may take a while depending on dataset size and hardware

4. START BACKEND SERVER
   Open a new terminal and run:
   
   cd backend
   npm install
   npm start
   
   Backend will start up

5. START FRONTEND
   Open another terminal and run:
   
   cd frontend
   npm install
   npm run dev
   
   Frontend will start up

Using the App
=====================
1. Open link to frontend in a browser
2. Type a player name in the search box
3. Click on a player from the dropdown suggestions
4. Wait for predictions to load from the backend
5. View the player's predicted statline for their next game

Notes
=====
- First run of fetch_data.py will take extra time due to API requests
- Player images are taken from NHL official assets; some historical players or players that changed teams may not have images available

Future Improvements?
===================
- Improving the model for better accuracy
- Adding goalie stats
- Adding features such as displaying team schedules and scores to help fantasy hockey managers
- Adding more player statistics (shooting %, +/-, etc.)
- Adding charts/graphs to show historical performance
- Adding the ability to use multiple seasons of data
- Adding player comparisons