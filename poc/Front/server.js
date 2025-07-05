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
        const clientToken = req.headers['x-auth-token'];
        
        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        if (!clientToken) {
            return res.status(401).json({ error: 'Authentication token required' });
        }

        // Forward the request to the FastAPI backend
        const apiUrl = process.env.API_URL || 'http://localhost:5000';
        
        console.log(`[FRONTEND] Forwarding to: ${apiUrl}/api/chat`);
        console.log(`[FRONTEND] Using client token: ${clientToken ? clientToken.substring(0, 10) + '...' : 'NOT SET'}`);
        
        const response = await fetch(`${apiUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${clientToken}`
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[FRONTEND] API Error ${response.status}:`, errorText);
            throw new Error(`Flask API error: ${response.status} - ${errorText}`);
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

// Get logs from FastAPI backend
app.get('/api/logs', async (req, res) => {
    try {
        const clientToken = req.headers['x-auth-token'];
        
        if (!clientToken) {
            return res.status(401).json({ error: 'Authentication token required' });
        }
        
        const apiUrl = process.env.API_URL || 'http://localhost:5000';
        const response = await fetch(`${apiUrl}/api/logs`, {
            headers: {
                'Authorization': `Bearer ${clientToken}`
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