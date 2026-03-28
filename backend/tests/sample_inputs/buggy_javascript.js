const express = require('express');
const fs = require('fs');
const app = express();

// Hardcoded secret - security issue
const JWT_SECRET = "mysupersecretkey123";
const API_KEY = "sk-prod-abc123xyz456";

app.use(express.json());

// XSS vulnerability - no sanitization
app.get('/search', (req, res) => {
    const query = req.query.q;
    // Directly injecting user input into HTML
    res.send(`<h1>Results for: ${query}</h1>`);
});

// Command injection vulnerability
app.post('/ping', (req, res) => {
    const { exec } = require('child_process');
    const host = req.body.host;
    // Never pass user input to exec!
    exec(`ping -c 4 ${host}`, (err, stdout) => {
        res.send(stdout);
    });
});

// No authentication check
app.delete('/users/:id', (req, res) => {
    const userId = req.params.id;
    // Anyone can delete any user!
    deleteUser(userId);
    res.send({ deleted: userId });
});

// Prototype pollution risk
function merge(target, source) {
    for (let key in source) {
        target[key] = source[key];  // No hasOwnProperty check
    }
    return target;
}

// Memory leak - event listener never removed
function startPolling() {
    setInterval(() => {
        process.on('data', (data) => {  // Adding listener in loop
            console.log(data);
        });
    }, 1000);
}

// Async error not handled
app.get('/file', (req, res) => {
    const filename = req.query.name;
    fs.readFile(filename, (err, data) => {
        // err not checked!
        res.send(data.toString());
    });
});

// Using == instead of ===
function isAdmin(role) {
    if (role == 1) {  // Type coercion bug
        return true;
    }
    return false;
}

// Sensitive data in logs
function loginUser(username, password) {
    console.log(`Login attempt: ${username} / ${password}`);  // Password logged!
    return username === "admin" && password === "password123";
}

app.listen(3000);
