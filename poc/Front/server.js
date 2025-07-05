const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

// Serve the main HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API endpoint to communicate with Python backend
app.post('/api/chat', async (req, res) => {
    try {
        const { message } = req.body;
        
        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        // Forward the request to the Flask API
        const apiUrl = process.env.API_URL || 'http://localhost:5000';
        const secretToken = process.env.SECRET_TOKEN || 'SECRET_TOKEN_WZ2l5TwbNE5GDndCOatlZTmkM1SILjwCZbN-kPPZtgg';
        const response = await fetch(`${apiUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Secret-Token': secretToken
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error(`Flask API error: ${response.status}`);
        }

        const data = await response.json();
        res.json(data);

    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Internal server error', details: error.message });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'Nico Clone Frontend is running' });
});

// Get logs from Flask API
app.get('/api/logs', async (req, res) => {
    try {
        const apiUrl = process.env.API_URL || 'http://localhost:5000';
        const secretToken = process.env.SECRET_TOKEN || 'SECRET_TOKEN_WZ2l5TwbNE5GDndCOatlZTmkM1SILjwCZbN-kPPZtgg';
        const response = await fetch(`${apiUrl}/api/logs`, {
            headers: {
                'X-Secret-Token': secretToken
            }
        });
        if (!response.ok) {
            throw new Error(`Flask API error: ${response.status}`);
        }
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Error fetching logs:', error);
        res.status(500).json({ error: 'Error fetching logs', details: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log('Nico Clone Frontend is ready!');
}); 